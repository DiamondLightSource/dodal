from typing import Generic, TypeVar

from bluesky.protocols import Locatable, Location
from ophyd_async.core import (
    AsyncStatus,
    OnOff,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_rw_rbv

"""
Note: See i11 cyberstar blower for implementation of Eurotherm Controller
"""


class AutoManual(StrictEnum):
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


_EUROTHERM_RBV: str = ":RBV"


class EurothermPID(StandardReadable):
    """The class for the Eurotherm PID values"""

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.P = epics_signal_rw_rbv(float, f"{prefix}P", _EUROTHERM_RBV)
            self.I = epics_signal_rw_rbv(float, f"{prefix}I", _EUROTHERM_RBV)
            self.D = epics_signal_rw_rbv(float, f"{prefix}D", _EUROTHERM_RBV)

        super().__init__(name)


class UpdatingEurothermPID(EurothermPID):
    """A Eurotherm PID controller that updates the PID values."""

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.update = epics_signal_rw(EurothermUpdate, f"{prefix}UPDATE.SCAN")

        super().__init__(prefix=prefix, name=name)


P = TypeVar("P", bound=EurothermPID)


class EurothermGeneral(StandardReadable, Locatable[float], Generic[P]):
    """A base class for any eurotherm controller."""

    def __init__(
        self,
        prefix: str,
        name: str = "",
        pid_class: type[P] = EurothermPID,
        temp_suffix: str = "PV:RBV",
    ):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.temp = epics_signal_r(float, f"{prefix}{temp_suffix}")

        with self.add_children_as_readables():
            self.setpoint = epics_signal_rw_rbv(float, f"{prefix}SP", _EUROTHERM_RBV)
            self.ramprate = epics_signal_rw_rbv(float, f"{prefix}RR", _EUROTHERM_RBV)
            self.output = epics_signal_rw_rbv(float, f"{prefix}O", _EUROTHERM_RBV)
            self.mode = epics_signal_rw_rbv(AutoManual, f"{prefix}MAN", _EUROTHERM_RBV)

        self.tune = pid_class(prefix=prefix)

        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        """Set the blower to a specific temperature."""
        await self.setpoint.set(value, wait=True)

    async def locate(self) -> Location[float]:
        setpoint = await self.setpoint.get_value()
        current_temp = await self.temp.get_value()
        location = Location(setpoint=setpoint, readback=current_temp)
        return location


class UpdatingEurothermGeneral(EurothermGeneral):
    """A Eurotherm controller that updates the setpoint and readback."""

    def __init__(self, prefix: str, name: str = ""):
        self.update = epics_signal_rw(EurothermUpdate, f"{prefix}UPDATE.SCAN")

        super().__init__(prefix=prefix, name=name, pid_class=UpdatingEurothermPID)


class EurothermAutotune(StandardReadable):
    """Newer versions of Eurotherm controllers have the ability to Autotune the
    PID values, and this is the device"""

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        with self.add_children_as_readables():
            self.control = epics_signal_rw(OnOff, f"{prefix}AUTOTUNE")
            self.high_limit = epics_signal_rw(float, f"{prefix}OUTPHI")
            self.low_limit = epics_signal_rw(float, f"{prefix}OUTPLO")

        super().__init__(name)
