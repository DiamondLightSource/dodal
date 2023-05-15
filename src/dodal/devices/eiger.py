from enum import Enum
from typing import Optional

from ophyd import Component, Device, EpicsSignalRO, Signal
from ophyd.areadetector.cam import EigerDetectorCam
from ophyd.status import AndStatus, Status, SubscriptionStatus

from dodal.devices.detector import DetectorParams
from dodal.devices.eiger_odin import EigerOdin
from dodal.devices.status import await_value
from dodal.log import LOGGER


class EigerTriggerMode(Enum):
    INTERNAL_SERIES = 0
    INTERNAL_ENABLE = 1
    EXTERNAL_SERIES = 2
    EXTERNAL_ENABLE = 3


class EigerTriggerNumber(str, Enum):
    MANY_TRIGGERS = "many_triggers"
    ONE_TRIGGER = "one_trigger"


class EigerDetector(Device):
    class ArmingSignal(Signal):
        def set(self, value, *, timeout=None, settle_time=None, **kwargs):
            return self.parent.async_stage()

    do_arm: ArmingSignal = Component(ArmingSignal)
    cam: EigerDetectorCam = Component(EigerDetectorCam, "CAM:")
    odin: EigerOdin = Component(EigerOdin, "")

    armed: bool = False

    stale_params: EpicsSignalRO = Component(EpicsSignalRO, "CAM:StaleParameters_RBV")
    bit_depth: EpicsSignalRO = Component(EpicsSignalRO, "CAM:BitDepthImage_RBV")

    STALE_PARAMS_TIMEOUT = 60

    filewriters_finished: SubscriptionStatus
    arming_status: Status

    detector_params: Optional[DetectorParams] = None

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
        self.arming_status = Status()
        self.odin.nodes.clear_odin_errors()
        status_ok, error_message = self.odin.check_odin_initialised()
        if not status_ok:
            raise Exception(f"Odin not initialised: {error_message}")

        if self.detector_params.use_roi_mode:
            self.enable_roi_mode()  # Chain starts here if using roi mode
        else:
            # So no callback error is raised (probably a neater way to do this)
            finished_status = Status()
            finished_status.set_finished()

            self.set_detector_threshold(
                energy=self.detector_params.current_energy, old_status=finished_status
            )  # Chain starts here if not using roi mode

    def unstage(self) -> bool:
        self.odin.file_writer.start_timeout.put(1)
        self.filewriters_finished.wait(30)
        if self.armed:
            self.disarm_detector()
        status_ok = self.odin.check_odin_state()
        self.disable_roi_mode()
        return status_ok

    def enable_roi_mode(self):
        self.change_roi_mode(True)

    def disable_roi_mode(self):
        self.change_roi_mode(False)

    def change_roi_mode(self, enable: bool):
        assert self.detector_params is not None
        detector_dimensions = (
            self.detector_params.detector_size_constants.roi_size_pixels
            if enable
            else self.detector_params.detector_size_constants.det_size_pixels
        )

        status = Status(timeout=10)
        status &= self.cam.roi_mode.set(1 if enable else 0)
        status &= self.odin.file_writer.image_height.set(detector_dimensions.height)
        status &= self.odin.file_writer.image_width.set(detector_dimensions.width)
        status &= self.odin.file_writer.num_row_chunks.set(detector_dimensions.height)
        status &= self.odin.file_writer.num_col_chunks.set(detector_dimensions.width)
        if enable:
            status.add_callback(
                lambda: self.set_detector_threshold(
                    energy=self.detector_params.current_energy,
                    old_status=status,
                )
            )

        else:
            # This part means unstaging is still blocking for now
            try:
                status.wait()
            except Exception:
                # Less specific logging message is currently read when enable = True, see check_callback_error()
                self.log.error("Failed to disable ROI mode")

    def set_cam_pvs(self, old_status) -> AndStatus:
        self.check_callback_error(old_status)
        assert self.detector_params is not None
        status = self.cam.acquire_time.set(
            self.detector_params.exposure_time, timeout=10
        )
        status &= self.cam.acquire_period.set(
            self.detector_params.exposure_time, timeout=10
        )
        status &= self.cam.num_exposures.set(1, timeout=10)
        status &= self.cam.image_mode.set(self.cam.ImageMode.MULTIPLE, timeout=10)
        status &= self.cam.trigger_mode.set(
            EigerTriggerMode.EXTERNAL_SERIES.value, timeout=10
        )
        status.add_callback(self.set_odin_pvs)

    def set_odin_pvs(self, old_status):
        self.check_callback_error(old_status)
        assert self.detector_params is not None
        status = self.odin.file_writer.num_frames_chunks.set(1, timeout=10)
        status.add_callback(self.set_odin_pvs_after_file_writer_set)

    def set_odin_pvs_after_file_writer_set(self, old_status):
        self.check_callback_error(old_status)
        file_prefix = self.detector_params.full_filename
        odin_status = self.odin.file_writer.file_path.set(
            self.detector_params.directory, timeout=10
        )
        odin_status &= self.odin.file_writer.file_name.set(file_prefix, timeout=10)

        odin_status &= await_value(self.odin.meta.file_name, file_prefix, 10)
        odin_status &= await_value(self.odin.file_writer.id, file_prefix, 10)

        odin_status.add_callback(self.set_mx_settings_pvs)

    def set_mx_settings_pvs(self, old_status):
        self.check_callback_error(old_status)
        assert self.detector_params is not None
        beam_x_pixels, beam_y_pixels = self.detector_params.get_beam_position_pixels(
            self.detector_params.detector_distance
        )
        status = self.cam.beam_center_x.set(beam_x_pixels)
        status &= self.cam.beam_center_y.set(beam_y_pixels)
        status &= self.cam.det_distance.set(self.detector_params.detector_distance)
        status &= self.cam.omega_start.set(self.detector_params.omega_start)
        status &= self.cam.omega_incr.set(self.detector_params.omega_increment)
        status.add_callback(self.set_num_triggers_and_captures)

    def set_detector_threshold(
        self, old_status: Status, energy: float, tolerance: float = 0.1
    ):
        """Ensures the energy threshold on the detector is set to the specified energy (in eV),
        within the specified tolerance.
        Args:
            energy (float): The energy to set (in eV)
            tolerance (float, optional): If the energy is already set to within
                this tolerance it is not set again. Defaults to 0.1eV.
        """

        self.check_callback_error(old_status)
        current_energy = self.cam.photon_energy.get()

        status = Status(timeout=10)

        if abs(current_energy - energy) > tolerance:
            status = self.cam.photon_energy.set(energy)
        else:
            status.set_finished()
        status.add_callback(self.set_cam_pvs)

    def set_num_triggers_and_captures(self, old_status):
        """Sets the number of triggers and the number of images for the Eiger to capture
        during the datacollection. The number of images is the number of images per
        trigger.
        """

        self.check_callback_error(old_status)
        assert self.detector_params is not None
        this_status = self.cam.num_images.set(
            self.detector_params.num_images_per_trigger, timeout=10
        )
        this_status &= self.cam.num_triggers.set(
            self.detector_params.num_triggers, timeout=10
        )
        this_status &= self.odin.file_writer.num_capture.set(
            self.detector_params.num_triggers
            * self.detector_params.num_images_per_trigger,
            timeout=10,
        )

        if not self.armed:
            this_status.add_callback(self.arm_detector)

    def wait_for_stale_parameters(self):
        this_status = await_value(self.stale_params, 0, 10)
        this_status.add_callback(self.wait_for_odin_status)

    def wait_for_odin_status(self, old_status):
        self.check_callback_error(old_status)
        self.forward_bit_depth_to_filewriter()
        this_status = self.odin.file_writer.capture.set(1, timeout=10)
        this_status &= await_value(self.odin.meta.ready, 1, 10)
        this_status.add_callback(self.wait_for_cam_acquire)

    def wait_for_cam_acquire(self, old_status):
        self.check_callback_error(old_status)
        LOGGER.info("Setting aquire")
        this_status = self.cam.acquire.set(1, timeout=10)
        this_status.add_callback(self.wait_fan_ready)

    def wait_fan_ready(self, old_status):
        LOGGER.info("Wait on fan ready")
        self.filewriters_finished = self.odin.create_finished_status()
        this_status = await_value(self.odin.fan.ready, 1, 10)
        this_status.add_callback(self.finish_arm)

    def finish_arm(self, old_status):
        self.check_callback_error(old_status)
        LOGGER.info("Finishing arm")
        self.armed = True
        self.arming_status.set_finished()

    def forward_bit_depth_to_filewriter(self):
        bit_depth = self.bit_depth.get()
        self.odin.file_writer.data_type.put(f"UInt{bit_depth}")

    def arm_detector(self, old_status) -> Status:
        self.check_callback_error(old_status)
        LOGGER.info("Waiting on stale parameters to go low")
        self.wait_for_stale_parameters()  # Starts the chain of arming functions

        return self.arming_status

    def disarm_detector(self):
        self.cam.acquire.put(0)
        self.armed = False

    def check_callback_error(self, status: Status):
        error = status.exception()
        if error is not None:
            LOGGER.error(f"{status} has failed with error {error}")
            raise error
