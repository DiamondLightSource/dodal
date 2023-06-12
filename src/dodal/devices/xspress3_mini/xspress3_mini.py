from enum import Enum

from ophyd import (
    Component,
    Device,
    EpicsSignal,
    EpicsSignalRO,
    EpicsSignalWithRBV,
    Signal,
)
from ophyd.status import Status

from dodal.devices.attenuator.attenuator import Attenuator
from dodal.devices.detector import DetectorParams
from dodal.devices.xspress3_mini.xspress3_mini_channel import (
    TimeSeriesValues,
    Xspress3MiniChannel,
)
from dodal.devices.zebra import Zebra
from dodal.log import LOGGER

# VERSION_3(SCA_UPDATE_TIME_SERIES_TEMPLATE, "Acquire", "Done", ""),


class AttenuationOptimisationFailedException(Exception):
    pass


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
    class ArmingSignal(Signal):
        def set(self, value, *, timeout=None, settle_time=None, **kwargs):
            return self.parent.arm()

    do_arm: ArmingSignal = Component(ArmingSignal)

    attenuator: Attenuator = Component(Attenuator, "-ATTN-01")

    zebra: Zebra = Component(
        Zebra, ""
    )  # TODO: these two devices won't work because prefixes don't start with
    # ~Xspress3mini  - move to bluesky plan?

    # Assume only one channel for now
    channel_1 = Component(Xspress3MiniChannel, "C1_")

    erase: EpicsSignal = Component(EpicsSignal, "ERASE")
    get_max_num_channels = Component(EpicsSignalRO, "MAX_NUM_CHANNELS_RBV")

    acquire: EpicsSignal = Component(EpicsSignal, "Acquire")

    get_roi_calc_mini: EpicsSignal = Component(EpicsSignal, "MCA1:Enable_RBV")

    NUMBER_ROIS_DEFAULT = 6

    trigger_mode_mini: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "TriggerMode")

    roi_start_x: EpicsSignal = Component(EpicsSignal, "ROISUM1:MinX")
    roi_size_x: EpicsSignal = Component(EpicsSignal, "ROISUM1:SizeX")
    acquire_time: EpicsSignal = Component(EpicsSignal, "AcquireTime")

    set_num_images: EpicsSignal = Component(EpicsSignal, ":NumImages")

    hdf_num_capture: EpicsSignal = Component(EpicsSignal, ":HDF5:NumCapture")

    squash_aux_dim: EpicsSignal = Component(EpicsSignal, ":DTC:SquashAuxDim")

    status_rbv: EpicsSignalRO = Component(EpicsSignalRO, ":DetectorState_RBV")

    writeHDF5Files = (
        False  # Not sure if this can ever be set true for attenuation optimising
    )

    def arm(self):  # do the arming logic here
        LOGGER.info("Arming Xspress3Mini detector...")
        self.trigger_mode.BURST
        self.pv_set_trigger_mode_mini.put(
            TriggerMode.BURST.value
        )  # TODO: decide if the trigger mode enum should be kept

        # Do erase (TODO: decide if this should be put into separate function)
        self.pv_erase.put(EraseState.Erase.value)

        do_start_status = self.do_start()

        do_start_status.wait(10)

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
        )  # In GDA this is blocking, but we can make asynchronous like with eiger

        status &= self.pv_acquire.set(AcquireState.ACQUIRE.value)

        return status

    def run_optimisation(
        self,
        optimisation_type,
        transmission,
        target,
        lower_limit,
        upper_limit,
        max_cycles,
        increment,
        low_roi=0,
        high_roi=0,
    ):
        # Might as well make everything here asynchronous eventually using stuff from eiger arming
        LOGGER.info("Starting Xspress3Mini optimisation routine")

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
            lower_limit: int
            upper_limit: int
            target: int

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

            # ------------------------arm Xpress3mini--------------------------
            LOGGER.info("Arming Xspress3Mini detector...")
            self.trigger_mode.BURST
            self.pv_set_trigger_mode_mini.put(
                TriggerMode.BURST.value
            )  # TODO: decide if the trigger mode enum should be kept

            # Do erase (TODO: decide if this should be put into separate function)
            self.pv_erase.put(EraseState.Erase.value)

            do_start_status = self.do_start()

            do_start_status.wait(10)

            # ----------------arming detector done--------------------------------

            # reset zebra first
            LOGGER.info("Resetting Zebra")
            self.zebra.pc.put(1)

            LOGGER.info("Arming Zebra")
            self.zebra.pc.arm().wait(30)

            data = self.channel_1.pv_latest_mca.get()  # this should return an array
            total_count = sum(data[low_roi:high_roi])

            LOGGER.info(f"Total count is {total_count}")

            if lower_limit <= total_count <= upper_limit:
                optimised_transmission = transmission
                LOGGER.info(
                    f"Total count is within accepted limits: {lower_limit}, {total_count}, {upper_limit}"
                )
                break

            old_transmission = transmission
            transmission = target / (total_count * old_transmission)

            if cycle == max_cycles - 1:
                raise AttenuationOptimisationFailedException(
                    f"Unable to optimise attenuation after maximum cycles.\
                                                             Total count is not within limits: {lower_limit} <= {total_count}\
                                                                  <= {upper_limit}"
                )

            self.attenuator.set_transmission(transmission)
            optimised_transmission = transmission

            LOGGER.info(f"Optimum transmission is {optimised_transmission}")

        """For dead time calc (do this once first part is working)
        
        # Read-out scaler values: Meant to do this a loop per channel, but there's only one channel right now
            total_time = self.channel_1.pv_time.get()
            reset_ticks = self.channel_1.pv_reset_ticks.get()

            LOGGER.info(
                f"Current total time = {total_time} \nCurrent reset ticks = {reset_ticks}"
            )

            deadtime = 0.0
            if reset_ticks != total_time:
                deadtime = 1 - (
                    abs(float(total_time - reset_ticks)) / float(total_time)
                )
        """
