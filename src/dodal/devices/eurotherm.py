from bluesky.protocols import Locatable, Location
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_rw_rbv

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


class EurothermGeneral(StandardReadable, Locatable[float]):
    """A base class for any eurotherm controller."""

    def __init__(
        self,
        prefix: str,
        name: str = "",
        setpoint_suffix: str = "SP",
        ramprate_suffix: str = "RR",
        output_suffix: str = "O",
        manual_suffix: str = "MAN",
        temp_suffix: str = "PV:RBV",
        rbv_suffix: str = ":RBV",
        update: bool = False,
    ):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.temp = epics_signal_r(float, f"{prefix}{temp_suffix}")

        with self.add_children_as_readables():
            self.setpoint = epics_signal_rw_rbv(
                float, f"{prefix}{setpoint_suffix}", rbv_suffix
            )
            self.ramprate = epics_signal_rw_rbv(
                float, f"{prefix}{ramprate_suffix}", rbv_suffix
            )
            self.output = epics_signal_rw_rbv(
                float, f"{prefix}{output_suffix}", rbv_suffix
            )
            self.mode = epics_signal_rw_rbv(
                ManualMode, f"{prefix}{manual_suffix}", rbv_suffix
            )

            if update:
                self.update = epics_signal_rw(EurothermUpdate, f"{prefix}UPDATE.SCAN")
            else:
                self.update = None

        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        """Set the blower to enabled"""
        await self.setpoint.set(value, wait=True)

    async def locate(self) -> Location[float]:
        setpoint = await self.setpoint.get_value()
        current_temp = await self.temp.get_value()
        location = Location(setpoint=setpoint, readback=current_temp)
        return location


class EurothermAutotune(StandardReadable):
    """Newer versions of Eurotherm controllers have the ability to Autotune the
    PID values, and this is the device"""

    def __init__(
        self,
        prefix: str,
        name: str = "",
        control_suffix: str = "AUTOTUNE",
        high_suffix: str = "OUTPHI",
        low_suffix: str = "OUTPLO",
    ):
        with self.add_children_as_readables():
            self.control = epics_signal_rw(AutotuneControl, f"{prefix}{control_suffix}")
            self.high_limit = epics_signal_rw(float, f"{prefix}{high_suffix}")
            self.low_limit = epics_signal_rw(float, f"{prefix}{low_suffix}")

        super().__init__(name)


class EurothermPID(StandardReadable):
    """The class for the Eurotherm PID values"""

    def __init__(self, prefix: str, name: str = "", rbv_suffix=":RBV", update=False):
        with self.add_children_as_readables():
            self.P = epics_signal_rw_rbv(float, f"{prefix}P", rbv_suffix)
            self.I = epics_signal_rw_rbv(float, f"{prefix}I", rbv_suffix)
            self.D = epics_signal_rw_rbv(float, f"{prefix}D", rbv_suffix)

            if update:
                self.update = epics_signal_rw(EurothermUpdate, f"{prefix}PID.SCAN")

        super().__init__(name)
