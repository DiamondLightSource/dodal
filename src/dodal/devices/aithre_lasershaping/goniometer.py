import asyncio
import math

import pytest
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
        z_component = math.cos(math.radians(omega))
        if z_component == pytest.approx(0):
            return sampy

        return sampz / math.cos(math.radians(omega))

    async def _set(self, value: float) -> None:
        omega = await self.omega.user_readback.get_value()
        z_component = value * math.cos(math.radians(omega))
        y_component = value * math.sin(math.radians(omega))
        await asyncio.gather(self.sampy.set(y_component), self.sampz.set(z_component))
