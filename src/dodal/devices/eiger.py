# type: ignore # Eiger will soon be ophyd-async https://github.com/DiamondLightSource/dodal/issues/700
from dataclasses import dataclass
from enum import Enum

from bluesky.protocols import Stageable
from ophyd import Component, Device, EpicsSignalRO, Signal
from ophyd.areadetector.cam import EigerDetectorCam
from ophyd.status import AndStatus, Status, StatusBase

from dodal.devices.detector import DetectorParams, TriggerMode
from dodal.devices.eiger_odin import EigerOdin
from dodal.devices.status import await_value
from dodal.devices.util.epics_util import run_functions_without_blocking
from dodal.log import LOGGER

FREE_RUN_MAX_IMAGES = 1000000


@dataclass
class EigerTimeouts:
    stale_params_timeout: int = 60
    general_status_timeout: int = 10
    meta_file_ready_timeout: int = 30
    all_frames_timeout: int = 120
    arming_timeout: int = 60


class InternalEigerTriggerMode(Enum):
    INTERNAL_SERIES = 0
    INTERNAL_ENABLE = 1
    EXTERNAL_SERIES = 2
    EXTERNAL_ENABLE = 3


AVAILABLE_TIMEOUTS = {
    "i03": EigerTimeouts(
        stale_params_timeout=60,
        general_status_timeout=20,
        meta_file_ready_timeout=30,
        all_frames_timeout=120,  # Long timeout for meta file to compensate for filesystem issues
        arming_timeout=60,
    )
}


class EigerDetector(Device, Stageable):
    class ArmingSignal(Signal):
        def set(self, value, *, timeout=None, settle_time=None, **kwargs):
            assert isinstance(self.parent, EigerDetector)
            return self.parent.async_stage()

    do_arm = Component(ArmingSignal)
    cam = Component(EigerDetectorCam, "CAM:")
    odin = Component(EigerOdin, "")

    stale_params = Component(EpicsSignalRO, "CAM:StaleParameters_RBV")
    bit_depth = Component(EpicsSignalRO, "CAM:BitDepthImage_RBV")

    filewriters_finished: StatusBase

    detector_params: DetectorParams | None = None

    arming_status = Status()
    arming_status.set_finished()

    disarming_status = Status()
    disarming_status.set_finished()

    def __init__(self, beamline: str = "i03", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.beamline = beamline
        # using i03 timeouts as default
        self.timeouts = AVAILABLE_TIMEOUTS.get(beamline, AVAILABLE_TIMEOUTS["i03"])

    @classmethod
    def with_params(
        cls,
        params: DetectorParams,
        name: str = "EigerDetector",
        beamline: str = "i03",
    ):
        det = cls(name=name, beamline=beamline)
        det.set_detector_parameters(params)
        return det

    def set_detector_parameters(self, detector_params: DetectorParams):
        self.detector_params = detector_params
        if self.detector_params is None:
            raise ValueError("Parameters for scan must be specified")

        to_check = [
            (
                self.detector_params.detector_size_constants is None,
                "Detector Size must be set",
            ),
            (
                self.detector_params.beam_xy_converter is None,
                "Beam converter must be set",
            ),
        ]

        errors = [message for check_result, message in to_check if check_result]

        if errors:
            raise Exception("\n".join(errors))

    def async_stage(self):
        self.odin.nodes.clear_odin_errors()
        status_ok, error_message = self.odin.wait_for_odin_initialised(
            self.timeouts.general_status_timeout
        )
        if not status_ok:
            raise Exception(f"Odin not initialised: {error_message}")

        self.arming_status = self.do_arming_chain()
        return self.arming_status

    def is_armed(self):
        return self.odin.fan.ready.get() == 1 and self.cam.acquire.get() == 1

    def wait_on_arming_if_started(self):
        if not self.arming_status.done:
            LOGGER.info("Waiting for arming to finish")
            self.arming_status.wait(self.timeouts.arming_timeout)

    def stage(self):
        self.wait_on_arming_if_started()
        if not self.is_armed():
            LOGGER.info("Eiger not armed, arming")

            self.async_stage().wait(timeout=self.timeouts.arming_timeout)

    def stop_odin_when_all_frames_collected(self):
        LOGGER.info("Waiting on all frames")
        try:
            await_value(
                self.odin.file_writer.num_captured,
                self.detector_params.full_number_of_images,
            ).wait(self.timeouts.all_frames_timeout)
        finally:
            LOGGER.info("Stopping Odin")
            self.odin.stop().wait(5)

    def unstage(self) -> bool:
        assert self.detector_params is not None
        try:
            self.disarming_status = Status()
            self.wait_on_arming_if_started()
            if self.detector_params.trigger_mode == TriggerMode.FREE_RUN:
                # In free run mode we have to manually stop odin
                self.stop_odin_when_all_frames_collected()

            self.odin.file_writer.start_timeout.set(1).wait(
                self.timeouts.general_status_timeout
            )
            LOGGER.info("Waiting on filewriter to finish")
            self.filewriters_finished.wait(30)

            LOGGER.info("Disarming detector")
        finally:
            self.disarm_detector()
            status_ok = self.odin.check_and_wait_for_odin_state(
                self.timeouts.general_status_timeout
            )
            self.disable_roi_mode().wait(self.timeouts.general_status_timeout)
        self.disarming_status.set_finished()
        return status_ok

    def stop(self, *args):
        """Emergency stop the device, mainly used to clean up after error."""
        LOGGER.info("Eiger stop() called - cleaning up...")
        if not self.disarming_status.done:
            LOGGER.info("Eiger still disarming, waiting on disarm")
            self.disarming_status.wait(self.timeouts.arming_timeout)
        else:
            self.wait_on_arming_if_started()
            stop_status = self.odin.stop()
            self.odin.file_writer.start_timeout.set(1).wait(
                self.timeouts.general_status_timeout
            )
            self.disarm_detector()
            stop_status &= self.disable_roi_mode()
            stop_status.wait(self.timeouts.general_status_timeout)
            # See https://github.com/DiamondLightSource/hyperion/issues/1395
            LOGGER.info("Turning off Eiger dev/shm streaming")
            self.odin.fan.dev_shm_enable.set(0).wait()
            LOGGER.info("Eiger has successfully been stopped")

    def disable_roi_mode(self):
        return self.change_roi_mode(False)

    def enable_roi_mode(self):
        return self.change_roi_mode(True)

    def change_roi_mode(self, enable: bool) -> StatusBase:
        assert self.detector_params is not None
        detector_dimensions = (
            self.detector_params.detector_size_constants.roi_size_pixels
            if enable
            else self.detector_params.detector_size_constants.det_size_pixels
        )

        status = self.cam.roi_mode.set(
            1 if enable else 0, timeout=self.timeouts.general_status_timeout
        )
        status &= self.odin.file_writer.image_height.set(
            detector_dimensions.height, timeout=self.timeouts.general_status_timeout
        )
        status &= self.odin.file_writer.image_width.set(
            detector_dimensions.width, timeout=self.timeouts.general_status_timeout
        )
        status &= self.odin.file_writer.num_row_chunks.set(
            detector_dimensions.height, timeout=self.timeouts.general_status_timeout
        )
        status &= self.odin.file_writer.num_col_chunks.set(
            detector_dimensions.width, timeout=self.timeouts.general_status_timeout
        )

        return status

    def set_cam_pvs(self) -> AndStatus:
        assert self.detector_params is not None
        status = self.cam.acquire_time.set(
            self.detector_params.exposure_time_s,
            timeout=self.timeouts.general_status_timeout,
        )
        status &= self.cam.acquire_period.set(
            self.detector_params.exposure_time_s,
            timeout=self.timeouts.general_status_timeout,
        )
        status &= self.cam.num_exposures.set(
            1, timeout=self.timeouts.general_status_timeout
        )
        status &= self.cam.image_mode.set(
            self.cam.ImageMode.MULTIPLE, timeout=self.timeouts.general_status_timeout
        )
        status &= self.cam.trigger_mode.set(
            InternalEigerTriggerMode.EXTERNAL_SERIES.value,
            timeout=self.timeouts.general_status_timeout,
        )
        return status

    def set_odin_number_of_frame_chunks(self) -> Status:
        assert self.detector_params is not None
        status = self.odin.file_writer.num_frames_chunks.set(
            1, timeout=self.timeouts.general_status_timeout
        )
        return status

    def set_odin_pvs(self) -> StatusBase:
        assert self.detector_params is not None
        file_prefix = self.detector_params.full_filename
        status = self.odin.file_writer.file_path.set(
            self.detector_params.directory, timeout=self.timeouts.general_status_timeout
        )
        status &= self.odin.file_writer.file_name.set(
            file_prefix, timeout=self.timeouts.general_status_timeout
        )
        status &= await_value(
            self.odin.meta.file_name,
            file_prefix,
            timeout=self.timeouts.general_status_timeout,
        )
        status &= await_value(
            self.odin.file_writer.id,
            file_prefix,
            timeout=self.timeouts.general_status_timeout,
        )
        return status

    def set_mx_settings_pvs(self):
        assert self.detector_params is not None
        beam_x_pixels, beam_y_pixels = self.detector_params.get_beam_position_pixels(
            self.detector_params.detector_distance
        )
        status = self.cam.beam_center_x.set(
            beam_x_pixels, timeout=self.timeouts.general_status_timeout
        )
        status &= self.cam.beam_center_y.set(
            beam_y_pixels, timeout=self.timeouts.general_status_timeout
        )
        status &= self.cam.det_distance.set(
            self.detector_params.detector_distance,
            timeout=self.timeouts.general_status_timeout,
        )
        status &= self.cam.omega_start.set(
            self.detector_params.omega_start,
            timeout=self.timeouts.general_status_timeout,
        )
        status &= self.cam.omega_incr.set(
            self.detector_params.omega_increment,
            timeout=self.timeouts.general_status_timeout,
        )
        return status

    def set_detector_threshold(self, energy: float, tolerance: float = 0.1) -> Status:
        """Ensures the energy threshold on the detector is set to the specified energy (in eV),
        within the specified tolerance.
        Args:
            energy (float): The energy to set (in eV)
            tolerance (float, optional): If the energy is already set to within
                this tolerance it is not set again. Defaults to 0.1eV.
        """

        current_energy = self.cam.photon_energy.get()
        if abs(current_energy - energy) > tolerance:
            return self.cam.photon_energy.set(
                energy, timeout=self.timeouts.general_status_timeout
            )
        else:
            status = Status()
            status.set_finished()
            return status

    def set_num_triggers_and_captures(self) -> StatusBase:
        """Sets the number of triggers and the number of images for the Eiger to capture
        during the datacollection. The number of images is the number of images per
        trigger.
        """

        assert self.detector_params is not None
        status = self.cam.num_images.set(
            self.detector_params.num_images_per_trigger,
            timeout=self.timeouts.general_status_timeout,
        )
        if self.detector_params.trigger_mode == TriggerMode.FREE_RUN:
            # The Eiger can't actually free run so we set a very large number of frames
            status &= self.cam.num_triggers.set(
                FREE_RUN_MAX_IMAGES, timeout=self.timeouts.general_status_timeout
            )
            # Setting Odin to write 0 frames tells it to write until externally stopped
            status &= self.odin.file_writer.num_capture.set(
                0, timeout=self.timeouts.general_status_timeout
            )
        elif self.detector_params.trigger_mode == TriggerMode.SET_FRAMES:
            status &= self.cam.num_triggers.set(
                self.detector_params.num_triggers,
                timeout=self.timeouts.general_status_timeout,
            )
            status &= self.odin.file_writer.num_capture.set(
                self.detector_params.full_number_of_images,
                timeout=self.timeouts.general_status_timeout,
            )

        return status

    def _wait_for_odin_status(self) -> StatusBase:
        self.forward_bit_depth_to_filewriter()
        await_value(self.odin.meta.active, 1).wait(self.timeouts.general_status_timeout)

        status = self.odin.file_writer.capture.set(
            1, timeout=self.timeouts.general_status_timeout
        )
        LOGGER.info("Eiger staging: awaiting odin metadata")
        status &= await_value(
            self.odin.meta.ready, 1, timeout=self.timeouts.meta_file_ready_timeout
        )
        return status

    def _wait_fan_ready(self) -> StatusBase:
        self.filewriters_finished = self.odin.create_finished_status()
        LOGGER.info("Eiger staging: awaiting odin fan ready")
        return await_value(self.odin.fan.ready, 1, self.timeouts.general_status_timeout)

    def _finish_arm(self) -> Status:
        LOGGER.info("Eiger staging: Finishing arming")
        status = Status()
        status.set_finished()
        return status

    def forward_bit_depth_to_filewriter(self):
        bit_depth = self.bit_depth.get()
        self.odin.file_writer.data_type.set(f"UInt{bit_depth}").wait(
            self.timeouts.general_status_timeout
        )

    def change_dev_shm(self, enable_dev_shm: bool):
        LOGGER.info(f"{'Enabling' if enable_dev_shm else 'Disabling'} dev shm")
        return self.odin.fan.dev_shm_enable.set(1 if enable_dev_shm else 0)

    def disarm_detector(self):
        self.cam.acquire.set(0).wait(self.timeouts.general_status_timeout)

    def do_arming_chain(self) -> Status:
        functions_to_do_arm = []
        assert self.detector_params
        detector_params: DetectorParams = self.detector_params
        if detector_params.use_roi_mode:
            functions_to_do_arm.append(self.enable_roi_mode)

        arming_sequence_funcs = [
            # If a beam dump occurs after arming the eiger but prior to eiger staging,
            # the odin may timeout which will cause the arming sequence to be retried;
            # if this previously completed successfully we must reset the odin first
            self.odin.stop,
            lambda: self.change_dev_shm(detector_params.enable_dev_shm),
            lambda: self.set_detector_threshold(detector_params.expected_energy_ev),
            self.set_cam_pvs,
            self.set_odin_number_of_frame_chunks,
            self.set_odin_pvs,
            self.set_mx_settings_pvs,
            self.set_num_triggers_and_captures,
            lambda: await_value(self.stale_params, 0, 60),
            self._wait_for_odin_status,
            lambda: self.cam.acquire.set(
                1, timeout=self.timeouts.general_status_timeout
            ),
            self._wait_fan_ready,
            self._finish_arm,
        ]

        functions_to_do_arm.extend(arming_sequence_funcs)

        return run_functions_without_blocking(functions_to_do_arm, associated_obj=self)
