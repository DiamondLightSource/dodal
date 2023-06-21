from enum import Enum
from typing import Callable

from ophyd import (
    Component,
    Device,
    EpicsSignal,
    EpicsSignalRO,
    EpicsSignalWithRBV,
    Signal,
)
from ophyd.status import Status

from dodal.devices.attenuator import Attenuator
from dodal.devices.detector import DetectorParams
from dodal.devices.status import await_value_in_list
from dodal.devices.xspress3_mini.xspress3_mini_channel import Xspress3MiniChannel
from dodal.devices.zebra import Zebra
from dodal.log import LOGGER


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


class DetectorState(Enum):
    ACQUIRE = "Acquire"
    CORRECT = "Correct"
    READOUT = "Readout"
    ABORTING = "Aborting"

    IDLE = "Idle"
    SAVING = "Saving"
    ERROR = "Error"
    INTILTIALIZING = "Initializing"
    DISCONNECTED = "Disconnected"
    ABORTED = "Aborted"


class Xspress3Mini(Device):
    class ArmingSignal(Signal):
        def set(self, value, *, timeout=None, settle_time=None, **kwargs):
            return self.parent.arm()

    class ReadArraySignal(Signal):
        """This signal is to allow array PVs to be read within Bluesky plans"""

        def set(self, value: Callable, *, timeout=None, settle_time=None, **kwargs):
            return value()

    do_arm: ArmingSignal = Component(ArmingSignal)

    read_array_signal: ReadArraySignal = Component(ReadArraySignal)

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

    # Should be one of these per channel
    dt_corrected_latest_mca: EpicsSignalRO = Component(EpicsSignalRO, ":ARR1:ArrayData")

    trigger_mode_mini: EpicsSignalWithRBV = Component(EpicsSignalWithRBV, "TriggerMode")
    roi_start_x: EpicsSignal = Component(EpicsSignal, "ROISUM1:MinX")
    roi_size_x: EpicsSignal = Component(EpicsSignal, "ROISUM1:SizeX")
    acquire_time: EpicsSignal = Component(EpicsSignal, "AcquireTime")

    set_num_images: EpicsSignal = Component(EpicsSignal, ":NumImages")

    hdf_num_capture: EpicsSignalWithRBV = Component(
        EpicsSignalWithRBV, ":HDF5:NumCapture"
    )

    squash_aux_dim: EpicsSignal = Component(EpicsSignal, ":DTC:SquashAuxDim")

    detector_state: EpicsSignalRO = Component(EpicsSignalRO, ":DetectorState_RBV")

    writeHDF5Files = (
        False  # Not sure if this can ever be set true for attenuation optimising
    )

    acquire_status: Status = None
    detector_busy_states = [
        DetectorState.ACQUIRE.value,
        DetectorState.CORRECT.value,
        DetectorState.ABORTING.value,
    ]

    def read_mca_dt_corrected_latest_mca(self):
        data = self.dt_corrected_latest_mca.get()
        return data

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
        self.pv_erase.put(EraseState.ERASE.value)
        pass

    """Other parameters that should be set somewhere (plan or ophyd?):
    deadtime threshold, collection time, transmission limits.
    """

    def stage(self):
        self.arm().wait(timeout=10)

    def do_start(self) -> Status:
        self.erase.put(EraseState.ERASE.value)
        status = self.channel_1.update_arrays.set(AcquireState.DONE.value)
        self.acquire_status = self.acquire.set(AcquireState.ACQUIRE.value)
        return status

    def arm(self) -> Status:
        LOGGER.info("Arming Xspress3Mini detector...")
        self.trigger_mode_mini.put(TriggerMode.BURST.value)
        self.do_start().wait(timeout=10)
        arm_status = await_value_in_list(self.detector_state, self.detector_busy_states)
        arm_status &= self.acquire_status
        return arm_status
