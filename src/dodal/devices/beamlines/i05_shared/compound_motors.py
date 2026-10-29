import asyncio

from bluesky.protocols import Locatable, Location, Stoppable
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_r,
    soft_signal_rw,
)
from ophyd_async.epics.motor import Motor


class PolynomCompoundMotors(
    StandardReadable,
    Locatable[float],
    Stoppable,
):
    """Compound motor that moves a slave according to a polynomial of the master.

    The slave position is calculated as:

        slave_position = offset + step * master_position
                        + square * master_position**2

    The polynomial coefficients (offset, step, and square) are exposed as
    writable soft signals and can be configured or changed at runtime.
    """

    def __init__(
        self,
        master: Motor,
        slave: Motor,
        offset: float = 0.0,
        step: float = 0.0,
        square: float = 0.0,
        name: str = "",
    ) -> None:
        self.master_ref = Reference(master)
        self.slave_ref = Reference(slave)

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            # Writable soft signals for configuring the polynomial.
            self.offset = soft_signal_rw(float, initial_value=offset)
            self.step = soft_signal_rw(float, initial_value=step)
            self.square = soft_signal_rw(float, initial_value=square)

            # Allow user to see what the device is configured as.
            self.master_name = derived_signal_r(
                self._read_master_name, dummy=self.offset
            )
            self.slave_name = derived_signal_r(self._read_slave_name, dummy=self.offset)

        # Expose motor readbacks as readables
        self.add_readables([master.user_readback, slave.user_readback])

        super().__init__(name=name)

    # https://github.com/bluesky/ophyd-async/issues/1471
    # Providing dummy signal needed due to bug.
    def _read_master_name(self, dummy: float) -> str:
        """Sync configured master device name."""
        return self.master_ref().name

    # https://github.com/bluesky/ophyd-async/issues/1471
    # Providing dummy signal needed due to bug.
    def _read_slave_name(self, dummy: float) -> str:
        """Sync configured slave device name."""
        return self.slave_ref().name

    @AsyncStatus.wrap
    async def set(self, new_position: float) -> None:
        offset, step, square = await asyncio.gather(
            self.offset.get_value(),
            self.step.get_value(),
            self.square.get_value(),
        )
        slave_position = offset + step * new_position + square * new_position**2

        await asyncio.gather(
            self.master_ref().set(new_position), self.slave_ref().set(slave_position)
        )

    async def stop(self, success: bool = False) -> None:
        await asyncio.gather(
            self.master_ref().stop(success), self.slave_ref().stop(success)
        )

    async def locate(self) -> Location[float]:
        return await self.master_ref().locate()
