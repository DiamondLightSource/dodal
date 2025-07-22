from ophyd_async.core import AsyncStatus, StrictEnum, set_and_wait_for_value
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.eurotherm import EurothermAutotune, EurothermGeneral, EurothermPID


class CyberstarBlowerEnable(StrictEnum):
    ON = "Enabled"
    OFF = "Disabled"


class CyberstarBlower(EurothermGeneral):
    """This is a specific device that uses a Eurotherm controller"""

    def __init__(
        self,
        prefix: str,
        name="",
        enable_suffix: str = "DISABLE",
        infix: str = "",
        update=False,
        autotune=False,
    ):
        with self.add_children_as_readables():
            self.enable = epics_signal_rw(
                CyberstarBlowerEnable, f"{prefix}{enable_suffix}"
            )
            self.tune = EurothermPID(prefix=prefix + infix, update=update)

            if autotune:
                self.autotune = EurothermAutotune(prefix=prefix + infix)

        super().__init__(prefix=prefix + infix, name=name, update=update)

    @AsyncStatus.wrap
    async def on(self):
        await set_and_wait_for_value(self.enable, CyberstarBlowerEnable.ON)

    @AsyncStatus.wrap
    async def off(self):
        await set_and_wait_for_value(self.enable, CyberstarBlowerEnable.OFF)

    @AsyncStatus.wrap
    async def set_ramp_rate(self, rate: float):
        await set_and_wait_for_value(self.ramprate, rate)

    @AsyncStatus.wrap
    async def set_setpoint(self, temp: float):
        await set_and_wait_for_value(self.setpoint, temp)
