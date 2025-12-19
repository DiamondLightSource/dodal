import abc
import asyncio

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    SignalRW,
    StandardReadable,
    StandardReadableFormat,
    soft_signal_rw,
)
from ophyd_async.epics.motor import Motor

from dodal.devices.insertion_device import MAXIMUM_MOVE_TIME, Apple2Controller
from dodal.log import LOGGER


class InsertionDeviceEnergyBase(abc.ABC, StandardReadable, Movable):
    """Base class for ID energy movable device."""

    def __init__(self, name: str = "") -> None:
        self.energy: Reference[SignalRW[float]]
        super().__init__(name=name)

    @abc.abstractmethod
    @AsyncStatus.wrap
    async def set(self, energy: float) -> None: ...


class BeamEnergy(StandardReadable, Movable[float]):
    """
    Compound device to set both ID and energy motor at the same time with an option to add an offset.
    """

    def __init__(
        self, id_energy: InsertionDeviceEnergyBase, mono: Motor, name: str = ""
    ) -> None:
        """
        Parameters
        ----------

        id_energy: InsertionDeviceEnergy
            An InsertionDeviceEnergy device.
        mono: Motor
            A Motor(energy) device.
        name:
            New device name.
        """
        super().__init__(name=name)
        self._id_energy = Reference(id_energy)
        self._mono_energy = Reference(mono)

        self.add_readables(
            [
                self._id_energy().energy(),
                self._mono_energy().user_readback,
            ],
            StandardReadableFormat.HINTED_SIGNAL,
        )

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.id_energy_offset = soft_signal_rw(float, initial_value=0)

    @AsyncStatus.wrap
    async def set(self, energy: float) -> None:
        LOGGER.info(f"Moving f{self.name} energy to {energy}.")
        await asyncio.gather(
            self._id_energy().set(
                energy=energy + await self.id_energy_offset.get_value()
            ),
            self._mono_energy().set(energy),
        )


class InsertionDeviceEnergy(InsertionDeviceEnergyBase):
    """Apple2 ID energy movable device."""

    def __init__(self, id_controller: Apple2Controller, name: str = "") -> None:
        self.energy = Reference(id_controller.energy)
        super().__init__(name=name)

        self.add_readables([self.energy()], StandardReadableFormat.HINTED_SIGNAL)

    @AsyncStatus.wrap
    async def set(self, energy: float) -> None:
        LOGGER.info(f"Setting insertion device energy to {energy}.")
        await self.energy().set(energy, timeout=MAXIMUM_MOVE_TIME)
