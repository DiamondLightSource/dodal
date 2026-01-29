import abc
import asyncio

from bluesky.protocols import Flyable, Movable, Preparable
from ophyd_async.core import (
    AsyncStatus,
    FlyMotorInfo,
    Reference,
    SignalRW,
    StandardReadable,
    StandardReadableFormat,
    WatchableAsyncStatus,
    error_if_none,
    soft_signal_rw,
)
from ophyd_async.epics.motor import Motor

from dodal.devices.insertion_device import (
    MAXIMUM_MOVE_TIME,
    Apple2Controller,
    Apple2Type,
)
from dodal.log import LOGGER


class InsertionDeviceEnergyBase(abc.ABC, StandardReadable, Movable):
    """Base class for ID energy movable device."""

    def __init__(self, name: str = "") -> None:
        self.energy: Reference[SignalRW[float]]
        super().__init__(name=name)

    @abc.abstractmethod
    @AsyncStatus.wrap
    async def set(self, energy: float) -> None: ...


class InsertionDeviceEnergy(InsertionDeviceEnergyBase, Preparable, Flyable):
    """Apple2 ID energy movable device."""

    def __init__(
        self, id_controller: Apple2Controller[Apple2Type], name: str = ""
    ) -> None:
        self.energy = Reference(id_controller.energy)
        self._id_controller = Reference(id_controller)
        super().__init__(name=name)

        self.add_readables([self.energy()], StandardReadableFormat.HINTED_SIGNAL)

    @AsyncStatus.wrap
    async def set(self, energy: float) -> None:
        LOGGER.info(f"Setting insertion device energy to {energy}.")
        await self.energy().set(energy, timeout=MAXIMUM_MOVE_TIME)

    @AsyncStatus.wrap
    async def prepare(self, value: FlyMotorInfo) -> None:
        """Convert FlyMotorInfo from energy to gap motion and move phase motor to mid point."""
        mid_energy = (value.start_position + value.end_position) / 2.0
        LOGGER.info(
            f"Preparing for fly energy scan, move {self._id_controller().apple2().phase} to {mid_energy}"
        )
        await self.set(energy=mid_energy)
        current_pol = await self._id_controller().polarisation_setpoint.get_value()
        start_position = self._id_controller().gap_energy_motor_converter(
            energy=value.start_position,
            pol=current_pol,
        )
        end_position = self._id_controller().gap_energy_motor_converter(
            energy=value.end_position, pol=current_pol
        )

        gap_fly_motor_info = FlyMotorInfo(
            start_position=start_position,
            end_position=end_position,
            time_for_move=value.time_for_move,
        )

        LOGGER.info(
            f"Flyscan info in energy: {value}. "
            + f"Flyscan info in gap: {gap_fly_motor_info}. "
            + f"Speed: {gap_fly_motor_info.velocity}."
        )
        await self._id_controller().apple2().gap().prepare(value=gap_fly_motor_info)

    @AsyncStatus.wrap
    async def kickoff(self):
        await self._id_controller().apple2().gap().kickoff()

    def complete(self) -> WatchableAsyncStatus:
        return self._id_controller().apple2().gap().complete()

    async def get_id_acceleration_time(self) -> float:
        return await self._id_controller().apple2().gap().acceleration_time.get_value()


class BeamEnergy(StandardReadable, Movable[float], Preparable, Flyable):
    """
    Compound device to set both ID and energy motor at the same time with an option to add an offset.
    """

    def __init__(
        self, id_energy: InsertionDeviceEnergy, mono: Motor, name: str = ""
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
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, energy: float) -> None:
        LOGGER.info(f"Moving f{self.name} energy to {energy}.")
        await asyncio.gather(
            self._id_energy().set(
                energy=energy + await self.id_energy_offset.get_value()
            ),
            self._mono_energy().set(energy),
        )

    @AsyncStatus.wrap
    async def prepare(self, value: FlyMotorInfo) -> None:
        await asyncio.gather(
            self._id_energy().prepare(value), self._mono_energy().prepare(value)
        )

    @AsyncStatus.wrap
    async def kickoff(self):
        pgm_acceleration_time, gap_acceleration_time = await asyncio.gather(
            self._mono_energy().acceleration_time.get_value(),
            self._id_energy().get_id_acceleration_time(),
        )
        start_offset_time = pgm_acceleration_time - gap_acceleration_time

        await self._mono_energy().kickoff()
        await asyncio.sleep(start_offset_time)
        await self._id_energy().kickoff()
        self._fly_status = self._combined_fly_status()

    def complete(self) -> AsyncStatus:
        """Stop when both pgm and id is done moving."""
        fly_status = error_if_none(self._fly_status, "kickoff not called")
        return fly_status

    @AsyncStatus.wrap
    async def _combined_fly_status(self):
        status_pgm = self._mono_energy().complete()
        status_id = self._id_energy().complete()
        await asyncio.gather(status_pgm, status_id)
