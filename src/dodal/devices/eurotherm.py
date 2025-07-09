from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw

"""
Note: See i11 cyberstar blower for implementation of Eurotherm Controller
"""


class AutotuneControl(StrictEnum):
    OFF = "Off"
    ON = "On"


class ManualMode(StrictEnum):
    AUTO = "Automatic"
    MANUAL = "Manual"


class EurothermUpdate(StrictEnum):
    PASSIVE = "Passive"
    EVENT = "Event"
    IO = "I/O Intr"
    S10 = "10 second"
    S5 = "5 second"
    S2 = "2 second"
    S1 = "1 second"
    S0_5 = ".5 second"
    S0_2 = ".2 second"
    S0_1 = ".1 second"


class EurothermGeneral(StandardReadable):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        setpoint_suffix: str = "SP",
        ramprate_suffix: str = "RR",
        output_suffix: str = "O",
        manual_suffix: str = "MAN",
        temp_suffix: str = "PV:RBV",
        update=False,
    ):
        self.setpoint = epics_signal_rw(float, f"{prefix}{setpoint_suffix}")
        self.ramprate = epics_signal_rw(float, f"{prefix}{ramprate_suffix}")
        self.output = epics_signal_rw(float, f"{prefix}{output_suffix}")
        self.mode = epics_signal_rw(ManualMode, f"{prefix}{manual_suffix}")
        self.temp = epics_signal_r(float, f"{prefix}{temp_suffix}")

        if update:
            self.update = epics_signal_rw(EurothermUpdate, f"{prefix}UPDATE.SCAN")

        super().__init__(name)


class EurothermAutotune(StandardReadable):
    def __init__(
        self,
        prefix: str,
        name: str = "",
        control_suffix: str = "AUTOTUNE",
        high_suffix: str = "OUTPHI",
        low_suffix: str = "OUTPLO",
    ):
        self.control = epics_signal_rw(AutotuneControl, f"{prefix}{control_suffix}")
        self.high_limit = epics_signal_rw(float, f"{prefix}{high_suffix}")
        self.low_limit = epics_signal_rw(float, f"{prefix}{low_suffix}")

        super().__init__(name)


class EurothermPID(StandardReadable):
    def __init__(self, prefix: str, name: str = "", update=False):
        self.P = epics_signal_rw(float, f"{prefix}P")
        self.I = epics_signal_rw(float, f"{prefix}I")
        self.D = epics_signal_rw(float, f"{prefix}D")

        if update:
            self.update = epics_signal_rw(EurothermUpdate, f"{prefix}PID.SCAN")

        super().__init__(name)
