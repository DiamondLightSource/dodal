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
    USER_COUNTDOWN = "USERCOUNTDN"
    BEAM_ENERGY = "BEAMENERGY"
    COUNTDOWN = "COUNTDOWN"
    END_COUNTDOWN = "ENDCOUNTDN"


class SynchrotronMode(StrictEnum):
    SHUTDOWN = "Shutdown"
    INJECTION = "Injection"
    NOBEAM = "No Beam"
    DEV = "Mach. Dev."
    USER = "User"
    SPECIAL = "Special"
    STARTUP = "BL Startup"
    UNKNOWN = "Unknown"


class Synchrotron(StandardReadable):
    """A StandardReadable device that represents a synchrotron facility, providing access to
    various synchrotron parameters and operational status.

    Args:
        signal_prefix (str, optional): Beamline part of PV. Defaults to Prefix.SIGNAL.
        status_prefix (str, optional): Status part of PV. Defaults to Prefix.STATUS.
        topup_prefix (str, optional): Top-up part of PV. Defaults to Prefix.TOP_UP.
        name (str, optional): Name of the device. Defaults to an empty string.

    Attributes:
        current (SignalR[float]): Read-only signal for the synchrotron beam current.
        energy (SignalR[float]): Read-only signal for the beam energy.
        probe (SignalR[str]): Read-only signal for the probe type. Defaults to ``"x-ray"``.
        type (SignalR[str]): Read-only signal for the synchrotron type. Defaults to ``"Synchrotron X-ray Source"``.
        synchrotron_mode (SignalR[SynchrotronMode]): Read-only signal for the current synchrotron operating mode.
        machine_user_countdown (SignalR[float]): Read-only signal for the machine user countdown timer.
        top_up_start_countdown (SignalR[float]): Read-only signal for the top-up start countdown timer.
        top_up_end_countdown (SignalR[float]): Read-only signal for the top-up end countdown timer.
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
            self.energy = epics_signal_r(float, status_prefix + Suffix.BEAM_ENERGY)

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.probe, _ = soft_signal_r_and_setter(str, initial_value="x-ray")
            self.type, _ = soft_signal_r_and_setter(
                str, initial_value="Synchrotron X-ray Source"
            )
            self.synchrotron_mode = epics_signal_r(
                SynchrotronMode, status_prefix + Suffix.MODE
            )
        self.machine_user_countdown = epics_signal_r(
            float, status_prefix + Suffix.USER_COUNTDOWN
        )
        self.top_up_start_countdown = epics_signal_r(
            float, topup_prefix + Suffix.COUNTDOWN
        )
        self.top_up_end_countdown = epics_signal_r(
            float, topup_prefix + Suffix.END_COUNTDOWN
        )

        super().__init__(name=name)
