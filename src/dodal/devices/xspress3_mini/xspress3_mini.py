from enum import Enum

from ophyd import Component, Device, EpicsSignal, EpicsSignalRO
from ophyd.status import Status

from dodal.devices.attenuator.attenuator import Attenuator
from dodal.devices.detector import DetectorParams
from dodal.devices.xspress3_mini.xspress3_mini_channel import (
    TimeSeriesValues,
    Xspress3MiniChannel,
)
from dodal.log import LOGGER

# VERSION_3(SCA_UPDATE_TIME_SERIES_TEMPLATE, "Acquire", "Done", ""),


class TriggerMode(Enum):
    SOFTWARE = "Software"
    HARDWARE = "Hardware"
    BURST = "Burst"
    TTL_Veto_Only = "TTL_Veto_Only"
    IDC = "IDC"
    SOTWARE_START_STOP = "Software_Start/Stop"
    TTL_BOTH = "TTL_Both"
    LVDS_VETO_ONLY = "LVDS_Veto_Only"
    LVDS_both = "LVDS_Both"


class UpdateRBV(Enum):
    DISABLED = "Disabled"
    ENABLED = "Enabled"


class EraseState(Enum):
    DONE = "Done"
    ERASE = "Erase"


class AcquireState(Enum):
    DONE = "Done"
    ACQUIRE = "Acquire"


class Xspress3Mini(Device):
    attenuator: Attenuator = Component(Attenuator, "-ATTN-01")

    # Assume only one channel for now
    channel_1 = Component(Xspress3MiniChannel, "C1_")

    pv_erase: EpicsSignal = Component(EpicsSignal, "ERASE")
    pv_get_max_num_channels = Component(EpicsSignalRO, "MAX_NUM_CHANNELS_RBV")

    pv_acquire: EpicsSignal = (Component(EpicsSignal, "Acquire"),)  #

    pv_get_roi_calc_mini: EpicsSignal = Component(EpicsSignal, "MCA1:Enable_RBV")

    NUMBER_ROIS_DEFAULT = 6

    pv_set_trigger_mode_mini: EpicsSignal = Component(EpicsSignal, "TriggerMode")

    pv_get_trig_mode_mini: EpicsSignalRO = Component(EpicsSignalRO, "TriggerMode_RBV")

    pv_roi_start_x: EpicsSignal = Component(EpicsSignal, "ROISUM1:MinX")
    pv_roi_size_x: EpicsSignal = Component(EpicsSignal, "ROISUM1:SizeX")
    pv_acquire_time: EpicsSignal = Component(EpicsSignal, "AcquireTime")

    pv_set_num_images: EpicsSignal = Component(EpicsSignal, ":NumImages")

    pv_hdf_num_capture: EpicsSignal = Component(EpicsSignal, ":HDF5:NumCapture")

    pv_squash_aux_dim: EpicsSignal = Component(EpicsSignal, ":DTC:SquashAuxDim")

    pv_status_rbv: EpicsSignalRO = Component(EpicsSignalRO, ":DetectorState_RBV")

    writeHDF5Files = (
        False  # Not sure if this can ever be set true for attenuation optimising
    )

    def attenuation_optimisation(self):
        pass

    # TODO: Make a DetectorParams thing with the correct parameters needed that matches the gda beamline_parameters.Parameters()
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

    def set_collection_time(self):
        pass

    def set_number_of_frames_to_collect(self, num_frames):
        """Controller.setnumframestoacquire(num_frames)
        if witehdf5Files:
            controller.sethdfnumframestoacquire(num_frames)
        """

        pass

    """Other parameters that should be set somewhere (plan or ophyd?):
    deadtime threshold, collection time, transmission limits.
    """

    deadtime_threshold: float
    collection_time: float
    transmission_limits: float
    optimisation_type: str

    def do_start(self) -> Status:
        # In GDA, doStart() calls doerase even though we call it just before

        #   Start time series (need to double check this bit is right)
        LOGGER.debug(
            f"Trying to set time series array control to {TimeSeriesValues.START_VALUE.value}"
        )
        # For each of the channels, we should fill its pv_sca5_update_mini with this value. But we only have one channel right now
        # Could generalise this for multiple channels if this is likely to ever occur
        status = self.channel_1.pv_sca5_update_mini.set(
            TimeSeriesValues.START_VALUE.value
        )

        self.pv_squash_aux_dim.put(
            UpdateRBV.ENABLED.value
        )  # In GDA this is blocking, but can make asynchronous like with eiger

        status &= self.pv_acquire.set(AcquireState.ACQUIRE.value)

        return status

    # Might as well make everything here asynchronous eventually using stuff from eiger arming

    def run_optimisation(self, low_roi=0, high_roi=0):
        LOGGER.info("Starting Xspress3Mini optimisation routine")
        optimisation_type = self.detector_params.optimisation_type
        if low_roi == 0:
            low_roi = self.detector_params.default_low_oi
        if high_roi == 0:
            high_roi = self.detector_params.default_high_roi

        LOGGER.info(
            f"Optimisation will be performed across ROI channels {low_roi} - {high_roi}"
        )

        # set collection time. Make
        self.pv_acquire_time.put(
            self.collection_time
        )  # could do wait instead of put, for async

        if optimisation_type == "total_counts":
            LOGGER.info("Using total count optimisation")

            # Get transmission, target, lower limit, upper limit, max cycles, optimised transmission from beamline_params
            max_cycles: int
            transmission: float

        for cycle in range(0, max_cycles):
            LOGGER.info(
                f"Setting transmission to {transmission} for attenuation optimisation cycle {cycle}"
            )

            self.attenuator.set_transmission(transmission)

            # Set number of frames to collect (could make a function). In GDA this block is done twice, but I'm pretty sure
            # that isn't useful
            self.pv_set_num_images.put(1)
            if self.writeHDF5Files:
                hdf_write_status = self.pv_hdf_num_capture.set(
                    1, timeout=10
                )  # TODO: check when we should wait for this status to complete

            # ------------------------armXpress3mini--------------------------
            LOGGER.info("Arming Xspress3Mini detector...")
            self.trigger_mode.BURST
            self.pv_set_trigger_mode_mini.put(
                TriggerMode.BURST.value
            )  # TODO: decide if the trigger mode enum should be kept

            # Do erase (TODO: decide if this should be put into separate function)
            self.pv_erase.put(EraseState.Erase.value)

            do_start_status = self.do_start()

            # final part of arming is waitForDetector()
        # ----------------arming done---------------------

        # self.zebraBoxPin.armXspress3MiniFluo_detector
        # self.zebraBoxPin.arm_zebra()
        # self.detector.waitUntilDetectorStateIsNotBusy()
