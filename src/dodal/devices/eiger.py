from enum import Enum
from typing import Optional

from ophyd import Component, Device, EpicsSignalRO, Signal
from ophyd.areadetector.cam import EigerDetectorCam
from ophyd.status import AndStatus, Status, SubscriptionStatus

from dodal.devices.detector import DetectorParams, TriggerMode
from dodal.devices.eiger_odin import EigerOdin
from dodal.devices.status import await_value
from dodal.devices.utils import run_functions_without_blocking
from dodal.log import LOGGER

FREE_RUN_MAX_IMAGES = 1000000


class InternalEigerTriggerMode(Enum):
    INTERNAL_SERIES = 0
    INTERNAL_ENABLE = 1
    EXTERNAL_SERIES = 2
    EXTERNAL_ENABLE = 3


class EigerDetector(Device):
    class ArmingSignal(Signal):
        def set(self, value, *, timeout=None, settle_time=None, **kwargs):
            return self.parent.async_stage()

    do_arm: ArmingSignal = Component(ArmingSignal)
    cam: EigerDetectorCam = Component(EigerDetectorCam, "CAM:")
    odin: EigerOdin = Component(EigerOdin, "")

    stale_params: EpicsSignalRO = Component(EpicsSignalRO, "CAM:StaleParameters_RBV")
    bit_depth: EpicsSignalRO = Component(EpicsSignalRO, "CAM:BitDepthImage_RBV")

    STALE_PARAMS_TIMEOUT = 60
    GENERAL_STATUS_TIMEOUT = 10
    ALL_FRAMES_TIMEOUT = 120

    filewriters_finished: SubscriptionStatus

    detector_params: Optional[DetectorParams] = None

    arming_status = Status()
    arming_status.set_finished()

    @classmethod
    def with_params(
        cls,
        params: DetectorParams,
        name: str = "EigerDetector",
        *args,
        **kwargs,
    ):
        det = cls(name=name, *args, **kwargs)
        det.set_detector_parameters(params)
        return det

    def set_detector_parameters(self, detector_params: DetectorParams):
        self.detector_params = detector_params
        if self.detector_params is None:
            raise Exception("Parameters for scan must be specified")

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
        status_ok, error_message = self.odin.check_odin_initialised()
        if not status_ok:
            raise Exception(f"Odin not initialised: {error_message}")

        self.arming_status = self.do_arming_chain()
        return self.arming_status

    def is_armed(self):
        return self.odin.fan.ready.get() == 1 and self.cam.acquire.get() == 1

    def wait_on_arming_if_started(self):
        if not self.arming_status.done:
            LOGGER.info("Waiting for arming to finish")
            self.arming_status.wait(60)

    def stage(self):
        self.wait_on_arming_if_started()
        if not self.is_armed():
            LOGGER.info("Eiger not armed, arming")
            self.async_stage().wait(timeout=self.GENERAL_STATUS_TIMEOUT)

    def stop_odin_when_all_frames_collected(self):
        LOGGER.info("Waiting on all frames")
        try:
            await_value(
                self.odin.file_writer.num_captured,
                self.detector_params.full_number_of_images,
            ).wait(self.ALL_FRAMES_TIMEOUT)
        finally:
            LOGGER.info("Stopping Odin")
            self.odin.stop().wait(5)

    def unstage(self) -> bool:
        assert self.detector_params is not None
        try:
            self.wait_on_arming_if_started()
            if self.detector_params.trigger_mode == TriggerMode.FREE_RUN:
                # In free run mode we have to manually stop odin
                self.stop_odin_when_all_frames_collected()

            self.odin.file_writer.start_timeout.put(1)
            LOGGER.info("Waiting on filewriter to finish")
            self.filewriters_finished.wait(30)

            LOGGER.info("Disarming detector")
        finally:
            self.disarm_detector()
            status_ok = self.odin.check_odin_state()
            self.disable_roi_mode()
        return status_ok

    def stop(self, *args):
        """Emergency stop the device, mainly used to clean up after error."""
        self.wait_on_arming_if_started()
        self.odin.stop()
        self.odin.file_writer.start_timeout.put(1)
        self.disarm_detector()
        self.disable_roi_mode()

    def disable_roi_mode(self):
        self.change_roi_mode(False)

    def change_roi_mode(self, enable: bool) -> Status:
        assert self.detector_params is not None
        detector_dimensions = (
            self.detector_params.detector_size_constants.roi_size_pixels
            if enable
            else self.detector_params.detector_size_constants.det_size_pixels
        )

        status = self.cam.roi_mode.set(
            1 if enable else 0, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        status &= self.odin.file_writer.image_height.set(
            detector_dimensions.height, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        status &= self.odin.file_writer.image_width.set(
            detector_dimensions.width, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        status &= self.odin.file_writer.num_row_chunks.set(
            detector_dimensions.height, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        status &= self.odin.file_writer.num_col_chunks.set(
            detector_dimensions.width, timeout=self.GENERAL_STATUS_TIMEOUT
        )

        return status

    def set_cam_pvs(self) -> AndStatus:
        assert self.detector_params is not None
        status = self.cam.acquire_time.set(
            self.detector_params.exposure_time, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        status &= self.cam.acquire_period.set(
            self.detector_params.exposure_time, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        status &= self.cam.num_exposures.set(1, timeout=self.GENERAL_STATUS_TIMEOUT)
        status &= self.cam.image_mode.set(
            self.cam.ImageMode.MULTIPLE, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        status &= self.cam.trigger_mode.set(
            InternalEigerTriggerMode.EXTERNAL_SERIES.value,
            timeout=self.GENERAL_STATUS_TIMEOUT,
        )
        return status

    def set_odin_number_of_frame_chunks(self) -> Status:
        assert self.detector_params is not None
        status = self.odin.file_writer.num_frames_chunks.set(
            1, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        return status

    def set_odin_pvs(self) -> Status:
        assert self.detector_params is not None
        file_prefix = self.detector_params.full_filename
        status = self.odin.file_writer.file_path.set(
            self.detector_params.directory, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        status &= self.odin.file_writer.file_name.set(
            file_prefix, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        status &= await_value(
            self.odin.meta.file_name, file_prefix, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        status &= await_value(
            self.odin.file_writer.id, file_prefix, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        return status

    def set_mx_settings_pvs(self):
        assert self.detector_params is not None
        beam_x_pixels, beam_y_pixels = self.detector_params.get_beam_position_pixels(
            self.detector_params.detector_distance
        )
        status = self.cam.beam_center_x.set(
            beam_x_pixels, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        status &= self.cam.beam_center_y.set(
            beam_y_pixels, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        status &= self.cam.det_distance.set(
            self.detector_params.detector_distance, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        status &= self.cam.omega_start.set(
            self.detector_params.omega_start, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        status &= self.cam.omega_incr.set(
            self.detector_params.omega_increment, timeout=self.GENERAL_STATUS_TIMEOUT
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
                energy, timeout=self.GENERAL_STATUS_TIMEOUT
            )
        else:
            status = Status()
            status.set_finished()
            return status

    def set_num_triggers_and_captures(self) -> Status:
        """Sets the number of triggers and the number of images for the Eiger to capture
        during the datacollection. The number of images is the number of images per
        trigger.
        """

        assert self.detector_params is not None
        status = self.cam.num_images.set(
            self.detector_params.num_images_per_trigger,
            timeout=self.GENERAL_STATUS_TIMEOUT,
        )
        if self.detector_params.trigger_mode == TriggerMode.FREE_RUN:
            # The Eiger can't actually free run so we set a very large number of frames
            status &= self.cam.num_triggers.set(
                FREE_RUN_MAX_IMAGES, timeout=self.GENERAL_STATUS_TIMEOUT
            )
            # Setting Odin to write 0 frames tells it to write until externally stopped
            status &= self.odin.file_writer.num_capture.set(
                0, timeout=self.GENERAL_STATUS_TIMEOUT
            )
        elif self.detector_params.trigger_mode == TriggerMode.SET_FRAMES:
            status &= self.cam.num_triggers.set(
                self.detector_params.num_triggers, timeout=self.GENERAL_STATUS_TIMEOUT
            )
            status &= self.odin.file_writer.num_capture.set(
                self.detector_params.full_number_of_images,
                timeout=self.GENERAL_STATUS_TIMEOUT,
            )

        return status

    def _wait_for_odin_status(self) -> Status:
        self.forward_bit_depth_to_filewriter()
        status = self.odin.file_writer.capture.set(
            1, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        LOGGER.info("Eiger staging: awaiting odin metadata")
        status &= await_value(
            self.odin.meta.ready, 1, timeout=self.GENERAL_STATUS_TIMEOUT
        )
        return status

    def _wait_fan_ready(self) -> Status:
        self.filewriters_finished = self.odin.create_finished_status()
        LOGGER.info("Eiger staging: awaiting odin fan ready")
        return await_value(self.odin.fan.ready, 1, self.GENERAL_STATUS_TIMEOUT)

    def _finish_arm(self) -> Status:
        LOGGER.info("Eiger staging: Finishing arming")
        return Status(done=True, success=True)

    def forward_bit_depth_to_filewriter(self):
        bit_depth = self.bit_depth.get()
        self.odin.file_writer.data_type.put(f"UInt{bit_depth}")

    def disarm_detector(self):
        self.cam.acquire.put(0)

    def do_arming_chain(self) -> Status:
        functions_to_do_arm = []
        detector_params: DetectorParams = self.detector_params
        if detector_params.use_roi_mode:
            functions_to_do_arm.append(lambda: self.change_roi_mode(enable=True))

        functions_to_do_arm.extend(
            [
                lambda: self.set_detector_threshold(
                    energy=detector_params.current_energy_ev
                ),
                self.set_cam_pvs,
                self.set_odin_number_of_frame_chunks,
                self.set_odin_pvs,
                self.set_mx_settings_pvs,
                self.set_num_triggers_and_captures,
                lambda: await_value(self.stale_params, 0, 60),
                self._wait_for_odin_status,
                lambda: self.cam.acquire.set(1, timeout=self.GENERAL_STATUS_TIMEOUT),
                self._wait_fan_ready,
                self._finish_arm,
            ]
        )

        return run_functions_without_blocking(functions_to_do_arm)
