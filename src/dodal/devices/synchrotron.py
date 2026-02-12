from enum import Enum

from ophyd_async.core import (
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.core import epics_signal_r


class Prefix(str, Enum):
    STATUS = "CS-CS-MSTAT-01:"
    TOP_UP = "SR-CS-FILL-01:"
    SIGNAL = "SR-DI-DCCT-01:"


class Suffix(str, Enum):
    SIGNAL = "SIGNAL"
    MODE = "MODE"
    USERCOUNTDOWN = "USERCOUNTDN"
    BEAMENERGY = "BEAMENERGY"
    COUNTDOWN = "COUNTDOWN"
    STACOUNTDN = "STACOUNTDN"
    ENDCOUNTDOWN = "ENDCOUNTDN"
    TOPUPSTATE = "TOPUPSTATE"
    FILLPERIOD = "FILLPERIOD"


class SynchrotronMode(StrictEnum):
    SHUTDOWN = "Shutdown"
    INJECTION = "Injection"
    NOBEAM = "No Beam"
    DEV = "Mach. Dev."
    USER = "User"
    SPECIAL = "Special"
    STARTUP = "BL Startup"
    UNKNOWN = "Unknown"


class TopUpState(StrictEnum):
    OFF = "Off"
    RUNNING = "Running"
    STOPPING = "Stopping"
    FAILED = "Failed"
    NO_PROCESS = "No process"


class Synchrotron(StandardReadable):
    """A StandardReadable device that represents a synchrotron facility, providing
    access to various synchrotron parameters and operational status.

    Args:
        signal_prefix (str, optional): Beamline part of PV. Defaults to Prefix.SIGNAL.
        status_prefix (str, optional): Status part of PV. Defaults to Prefix.STATUS.
        topup_prefix (str, optional): Top-up part of PV. Defaults to Prefix.TOP_UP.
        name (str, optional): Name of the device. Defaults to an empty string.

    Attributes:
        current (SignalR[float]): Read-only signal for the synchrotron ring current.
            Standard optional field in NXsource component of nexus file.
        energy (SignalR[float]): Read-only signal for the synchrotron ring energy.
            Standard optional field in NXsource component of nexus file.
        probe (SignalR[str]): Read-only signal for the probe type. Defaults to
            ``"x-ray"``. Standard optional field in NXsource component of nexus file.
        type (SignalR[str]): Read-only signal for the synchrotron type. Defaults to
            ``"Synchrotron X-ray Source"``. Standard optional field in NXsource
            component of nexus file.
        synchrotron_mode (SignalR[SynchrotronMode]): current state of the synchrotron
            ring. Standard optional field ``"mode"`` in NXsource component of nexus file.
        machine_user_countdown (SignalR[float]): If current mode in user, counts down
            the number of seconds until the end of the current period.
        top_up_start_countdown (SignalR[float]): counter that runs to zero at the start
            of TopUp and remains there until the fill is complete when it resets to time
            before next TopUp fill. Used in data acquisition to avoid beam intensity
            change during topup.
        top_up_countdown (SignalR[float]): counter that runs to zero at the start
            of TopUp fill and is reset immediately to the time to next TopUp fill once
            TopUp starts.
        top_up_end_countdown (SignalR[float]): counter that runs to zero at the end of
            TopUp fill and resets immediately to an estimate of the time before the end
            of the next TopUp fill. Used in data acquisition to avoid beam intensity
            change during topup.
        fill_period (signalR[float]): time between TopUp (in minutes).Used in data
            acquisition to monitor synchrotron state.
        top_up_state (signalR[TopUpState]): state of the TopUp process. Used in data
            acquisition to confirm state.
    """

    def __init__(
        self,
        signal_prefix: str = Prefix.SIGNAL,
        status_prefix: str = Prefix.STATUS,
        topup_prefix: str = Prefix.TOP_UP,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.current = epics_signal_r(float, signal_prefix + Suffix.SIGNAL)
            self.energy = epics_signal_r(float, status_prefix + Suffix.BEAMENERGY)

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.probe, _ = soft_signal_r_and_setter(str, initial_value="x-ray")
            self.type, _ = soft_signal_r_and_setter(
                str, initial_value="Synchrotron X-ray Source"
            )
            self.synchrotron_mode = epics_signal_r(
                SynchrotronMode, status_prefix + Suffix.MODE
            )
        self.machine_user_countdown = epics_signal_r(
            float, status_prefix + Suffix.USERCOUNTDOWN
        )
        self.top_up_start_countdown = epics_signal_r(
            float, topup_prefix + Suffix.COUNTDOWN
        )
        self.top_up_countdown = epics_signal_r(float, topup_prefix + Suffix.STACOUNTDN)
        self.top_up_end_countdown = epics_signal_r(
            float, topup_prefix + Suffix.ENDCOUNTDOWN
        )
        self.fill_period = epics_signal_r(float, topup_prefix + Suffix.FILLPERIOD)
        self.top_up_state = epics_signal_r(TopUpState, topup_prefix + Suffix.TOPUPSTATE)
        super().__init__(name=name)
