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
    def __init__(
        self,
        prefix: str = "",
        name: str = "synchrotron",
        *,
        signal_prefix=Prefix.SIGNAL,
        status_prefix=Prefix.STATUS,
        topup_prefix=Prefix.TOP_UP,
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
