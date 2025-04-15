import asyncio
import math

from ophyd_async.core import StandardReadable, derived_signal_rw
from ophyd_async.epics.motor import Motor


class Goniometer(StandardReadable):
    """Goniometer and the stages it sits on"""

    def __init__(self, prefix: str, name: str = "") -> None:
        self.x = Motor(prefix + "X")
        self.y = Motor(prefix + "Y")
        self.z = Motor(prefix + "Z")
        self.sampy = Motor(prefix + "SAMPY")
        self.sampz = Motor(prefix + "SAMPZ")
        self.omega = Motor(prefix + "OMEGA")
        self.vertical_position = derived_signal_rw(
            self._get,
            self._set,
            sampy=self.sampy,
            sampz=self.sampz,
            omega=self.omega,
        )
        super().__init__(name)

    def _get(self, sampz: float, sampy: float, omega: float) -> float:
        z_component = sampz * math.cos(math.radians(omega))
        y_component = sampy * math.sin(math.radians(omega))
        return z_component + y_component

    async def _set(self, value: float) -> None:
        omega = await self.omega.user_readback.get_value()
        z_component = value * math.cos(math.radians(omega))
        y_component = value * math.sin(math.radians(omega))
        await asyncio.gather(self.y.set(y_component), self.z.set(z_component))
