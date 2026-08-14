import asyncio

from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.beamlines.i06_1.magnet.coordinates import MagnetRequest
from dodal.devices.beamlines.i06_1.magnet.enums import MagnetMode
from dodal.devices.beamlines.i06_1.magnet.movement import MagnetPositionError
from dodal.devices.beamlines.i06_1.magnet.ramp_controller import (
    MagnetAxisRampRateController,
)


class MagnetAxisPowerSupply(StandardReadable):
    """Power supply interface for a single magnet axis.

    Exposes the configured field limit and ramp rate controller for one axis and
    provides validation that requested field values do not exceed the current
    hardware limit.
    """

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.limit = epics_signal_rw(float, prefix + "LIM:FIELD:NOW")
            self.ramp_rate = MagnetAxisRampRateController(prefix)

        super().__init__(name)

    async def check_axis_with_limit(
        self, pos: float | None, mode: MagnetMode, axis: str
    ):
        if pos is None:
            return
        limit = await self.limit.get_value()
        if pos > limit:
            raise MagnetPositionError.axis_outside_limit(mode, limit, pos, axis)


class ThreeMagnetAxisPowerSupply(StandardReadable):
    """Power supply interfaces for the X, Y and Z magnet axes.

    Groups the individual axis power supplies and provides validation of a
    cartesian magnet request against the configured hardware limits of each axis.
    """

    def __init__(self, prefix: str, name: str = ""):

        with self.add_children_as_readables():
            self.x = MagnetAxisPowerSupply(prefix + "-01:")
            self.y = MagnetAxisPowerSupply(prefix + "-02:")
            self.z = MagnetAxisPowerSupply(prefix + "-03:")

        super().__init__(name)

    async def check_axes_within_limit(self, pos: MagnetRequest, mode: MagnetMode):
        await asyncio.gather(
            self.x.check_axis_with_limit(pos.x, mode, MagnetMode.UNIAXIAL_X.axis_alias),
            self.y.check_axis_with_limit(pos.y, mode, MagnetMode.UNIAXIAL_Y.axis_alias),
            self.z.check_axis_with_limit(pos.z, mode, MagnetMode.UNIAXIAL_Z.axis_alias),
        )
