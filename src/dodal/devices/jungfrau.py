from ophyd_async.core import (
    DetectorTrigger,
    Device,
    PathProvider,
    SignalR,
    SignalRW,
    SignalX,
    StandardDetector,
    StrictEnum,
    soft_signal_rw,
)
from ophyd_async.epics.odin import Odin, OdinWriter
from ophyd_async.fastcs.core import fastcs_connector
from ophyd_async.fastcs.jungfrau._controller import JungfrauController
from pydantic import NonNegativeInt


class JungfrauTriggerMode(StrictEnum):
    INTERNAL = "Internal"

    # Detector waits for external trigger to start frame series, but still
    # controls exposure time and frame period internally
    EXTERNAL = "External"


class DetectorStatus(StrictEnum):
    IDLE = "Idle"
    ERROR = "Error"
    WAITING = "Waiting"
    RUN_FINISHED = "RunFinished"
    TRANSMITTING = "Transmitting"
    RUNNING = "Running"
    STOPPED = "Stopped"


class GainMode(StrictEnum):
    DYNAMIC = "Dynamic"
    FORCE_SWITCH_G1 = "ForceSwitchG1"
    FORCE_SWITCH_G2 = "ForceSwitchG2"
    FIX_G1 = "FixG1"
    FIX_G2 = "FixG2"

    # Use with caution - this may damage the detector
    FIX_G0 = "FixG0"


class PedestalMode(StrictEnum):
    ON = "On"
    OFF = "Off"


class AcquisitionType(StrictEnum):
    STANDARD = "Standard"
    PEDESTAL = "Pedestal"


JUNGFRAU_TRIGGER_MODE_MAP = {
    DetectorTrigger.EDGE_TRIGGER: JungfrauTriggerMode.EXTERNAL,
    DetectorTrigger.INTERNAL: JungfrauTriggerMode.INTERNAL,
}


class JungfrauDriverIO(Device):
    """Contains signals for handling IO on the Jungfrau detector."""

    exposure_time: SignalRW[float]  # in s

    # Includes deadtime
    period_between_frames: SignalRW[float]  # in s

    # Sets the delay for the beginning of the exposure time after
    # trigger input
    delay_after_trigger: SignalRW[float]  # in s

    # In internal trigger mode, this is frames per trigger. In external trigger mode,
    # this is frames per overall acquisition. In pedestal mode, this signal is not set.
    frames_per_acq: SignalRW[NonNegativeInt]

    pedestal_mode: SignalRW[PedestalMode]  # this used to be called pedestal_mode_state
    pedestal_mode_frames: SignalRW[NonNegativeInt]
    pedestal_mode_loops: SignalRW[NonNegativeInt]

    gain_mode: SignalRW[GainMode]

    acquisition_start: SignalX

    acquisition_stop: SignalX
    bit_depth: SignalR[int]
    trigger_mode: SignalRW[JungfrauTriggerMode]
    detector_status: SignalR[DetectorStatus]

    def __init__(self, uri: str, name: str = ""):
        # Determines how the TriggerInfo gets mapped to the Jungfrau during prepare
        self.acquisition_type = soft_signal_rw(
            AcquisitionType, AcquisitionType.STANDARD
        )
        super().__init__(name=name, connector=fastcs_connector(self, uri))


class Jungfrau(StandardDetector[JungfrauController, OdinWriter]):
    """Ophyd-async implementation of a Jungfrau Detector."""

    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        drv_suffix: str,
        hdf_suffix: str,
        odin_nodes: int,
        name="",
    ):
        self.drv = JungfrauDriverIO(prefix + drv_suffix)
        self.odin = Odin(prefix + hdf_suffix, nodes=odin_nodes)
        writer = OdinWriter(
            path_provider,
            self.odin,
            self.drv.bit_depth,
        )
        controller = JungfrauController(self.drv)  # type: ignore
        super().__init__(controller, writer, name=name)
