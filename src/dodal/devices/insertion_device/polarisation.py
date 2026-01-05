import asyncio

from bluesky.protocols import Locatable, Location
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadable,
    StandardReadableFormat,
)

from dodal.devices.insertion_device import MAXIMUM_MOVE_TIME, Apple2Controller
from dodal.devices.insertion_device.enum import Pol
from dodal.log import LOGGER


class InsertionDevicePolarisation(StandardReadable, Locatable[Pol]):
    """Apple2 ID polarisation movable device."""

    def __init__(self, id_controller: Apple2Controller, name: str = "") -> None:
        self.polarisation = Reference(id_controller.polarisation)
        self.polarisation_setpoint = Reference(id_controller.polarisation_setpoint)
        super().__init__(name=name)

        self.add_readables([self.polarisation()], StandardReadableFormat.HINTED_SIGNAL)

    @AsyncStatus.wrap
    async def set(self, pol: Pol) -> None:
        LOGGER.info(f"Setting insertion device polarisation to {pol.name}")
        await self.polarisation().set(pol, timeout=MAXIMUM_MOVE_TIME)

    async def locate(self) -> Location[Pol]:
        """Return the current polarisation"""
        setpoint, readback = await asyncio.gather(
            self.polarisation_setpoint().get_value(), self.polarisation().get_value()
        )
        return Location(setpoint=setpoint, readback=readback)
