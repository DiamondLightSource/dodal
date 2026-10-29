import asyncio
from dataclasses import dataclass
from functools import cached_property
from typing import TypeVar

from ophyd_async.core import (
    DeviceMock,
    MovableLogic,
    Reference,
    SignalR,
    StandardMovable,
    StandardReadable,
    StandardReadableFormat,
    TimeoutCalculator,
    default_mock_class,
    derived_signal_r,
    soft_signal_rw,
)

StandardMovableT = TypeVar("StandardMovableT", bound=StandardMovable[float])


@dataclass
class PolyCompoundMotorMovableLogic(MovableLogic):
    master: StandardMovable[float]
    slave: StandardMovable[float]
    offset: SignalR[float]
    step: SignalR[float]
    square: SignalR[float]

    def _calc_slave_pos(
        self, new_pos: float, offset: float, step: float, square: float
    ) -> float:
        return offset + step * new_pos + square * new_pos**2

    async def move(self, new_position: float, timeout: TimeoutCalculator) -> None:
        offset, step, square = await asyncio.gather(
            self.offset.get_value(),
            self.step.get_value(),
            self.square.get_value(),
        )
        slave_pos = self._calc_slave_pos(
            new_pos=new_position, offset=offset, step=step, square=square
        )
        await asyncio.gather(self.master.set(new_position), self.slave.set(slave_pos))

    async def stop(self) -> None:
        await asyncio.gather(self.master.stop(), self.slave.stop())


@default_mock_class(DeviceMock)
class PolynomCompoundMotors(
    StandardMovable[float],
    StandardReadable,
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
        master: StandardMovable[float],
        slave: StandardMovable[float],
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

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            # This is needed so that StandardMovable doesn't rename the master readback
            # signal to this device name.
            self.readback = derived_signal_r(
                self._readback_read, readback=master.movable_logic.readback
            )

        # Expose motor readbacks as readables
        self.add_readables(
            [master.movable_logic.readback, slave.movable_logic.readback]
        )

        super().__init__(name=name)

    def _readback_read(self, readback: float) -> float:
        return readback

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

    @cached_property
    def movable_logic(self) -> MovableLogic:
        return PolyCompoundMotorMovableLogic(
            readback=self.readback,
            setpoint=self.master_ref().movable_logic.setpoint,
            master=self.master_ref(),
            slave=self.slave_ref(),
            offset=self.offset,
            step=self.step,
            square=self.square,
        )
