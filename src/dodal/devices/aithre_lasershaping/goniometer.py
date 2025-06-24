import asyncio
import math

from ophyd_async.core import derived_signal_rw
from ophyd_async.epics.motor import Motor

from dodal.devices.motors import XYZStage


class Goniometer(XYZStage):
    """The Aithre lab goniometer and the XYZ stage it sits on.

    `x`, `y` and `z` control the axes of the positioner at the base, while `sampy` and
    `sampz` control the positioner of the sample. `omega` is the rotation about the
    x-axis (along the length of the sample holder).

    The `vertical_position` signal refers to the height of the sample from the point of
    view of the OAV and setting this value moves the sample vertically in the OAV plane
    regardless of the current rotation.
    """

    def __init__(self, prefix: str, name: str = "") -> None:
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
        await asyncio.gather(
            self.sampy.set(y_component),
            self.sampz.set(z_component),
            self.omega.set(omega),
        )
