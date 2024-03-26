from enum import Enum

from ophyd_async.core import StandardReadable
from ophyd_async.epics.signal import epics_signal_r


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


class SynchrotronMode(str, Enum):
    SHUTDOWN = "Shutdown"
    INJECTION = "Injection"
    NOBEAM = "No Beam"
    DEV = "Mach. Dev."
    USER = "User"
    SPECIAL = "Special"
    STARTUP = "BL Startup"
    UNKNOWN = "Unknown"


class Synchrotron(StandardReadable):
    def __init__(
        self,
        prefix: str = "",
        name: str = "synchrotron",
        *,
        signal_prefix=Prefix.SIGNAL,
        status_prefix=Prefix.STATUS,
        topup_prefix=Prefix.TOP_UP,
    ):
        self.ring_current = epics_signal_r(float, signal_prefix + Suffix.SIGNAL)
        self.synchrotron_mode = epics_signal_r(
            SynchrotronMode, status_prefix + Suffix.MODE
        )
        self.machine_user_countdown = epics_signal_r(
            float, status_prefix + Suffix.USER_COUNTDOWN
        )
        self.beam_energy = epics_signal_r(float, status_prefix + Suffix.BEAM_ENERGY)
        self.topup_start_countdown = epics_signal_r(
            float, topup_prefix + Suffix.COUNTDOWN
        )
        self.top_up_end_countdown = epics_signal_r(
            float, topup_prefix + Suffix.END_COUNTDOWN
        )

        self.set_readable_signals(
            read=[
                self.ring_current,
                self.machine_user_countdown,
                self.topup_start_countdown,
                self.top_up_end_countdown,
            ],
            config=[
                self.beam_energy,
                self.synchrotron_mode,
            ],
        )
        super().__init__(name=name)
