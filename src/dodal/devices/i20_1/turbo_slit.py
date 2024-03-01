import asyncio
import time
from enum import Enum
from typing import Callable, List, Optional

from bluesky.protocols import Configurable, Movable, Stageable, Stoppable
from ophyd_async.core import AsyncStatus, Device, StandardReadable
from ophyd_async.epics.motion.motor import Motor

from dodal.devices.util.epics_util import epics_signal_put_wait


class ControlEnumMotor(StandardReadable, Movable, Stoppable):
    """Device that moves a motor record"""

    def __init__(self, prefix: str, name="") -> None:
        # Define some signals
        self.setpoint = epics_signal_put_wait(ControlEnum, prefix + ".VAL")
        self.readback = epics_signal_r(ControlEnum, prefix + ".RBV")
        self.stop_ = epics_signal_x(prefix + ".STOP")
        self.set_readable_signals(
            read=[self.readback],
            config=[],
        )
        super().__init__(name=name)

    def set_name(self, name: str):
        super().set_name(name)
        # Readback should be named the same as its parent in read()
        self.readback.set_name(name)

    async def _move(self, new_position: float, watchers: List[Callable] = []):
        self._set_success = True
        start = time.monotonic()
        old_position, units, precision = await asyncio.gather(
            self.setpoint.get_value(),
        )

        def update_watchers(current_position: float):
            for watcher in watchers:
                watcher(
                    name=self.name,
                    current=current_position,
                    initial=old_position,
                    target=new_position,
                    time_elapsed=time.monotonic() - start,
                )

        self.readback.subscribe_value(update_watchers)
        try:
            await self.setpoint.set(new_position)
        finally:
            self.readback.clear_sub(update_watchers)
        if not self._set_success:
            raise RuntimeError("Motor was stopped")

    def move(self, new_position: ControlEnum, timeout: Optional[float] = None):
        """Commandline only synchronous move of a Motor"""
        from bluesky.run_engine import call_in_bluesky_event_loop, in_bluesky_event_loop

        if in_bluesky_event_loop():
            raise RuntimeError("Will deadlock run engine if run in a plan")
        call_in_bluesky_event_loop(self._move(new_position), timeout)  # type: ignore

    def set(
        self, new_position: ControlEnum, timeout: Optional[float] = None
    ) -> AsyncStatus:
        watchers: List[Callable] = []
        # todo here string or float?
        coro = asyncio.wait_for(self._move(new_position, watchers), timeout=timeout)
        return AsyncStatus(coro, watchers)

    async def stop(self, success=False):
        self._set_success = success
        # Put with completion will never complete as we are waiting for completion on
        # the move above, so need to pass wait=False
        status = self.stop_.trigger(wait=False)
        await status


class StandardMovable(Device, Movable, Configurable, Stageable):
    pass


class TestDetector(StandardReadable):
    pass


class ControlEnum(str, Enum):
    value1 = "close"
    value2 = "open"


class TurboSlit(StandardMovable):
    """
    todo for now only the x motor
    add soft limits
    check min speed
    set speed back to before movement
    """

    # motor_x = Motor(prefix="BL20J-OP-PCHRO-01:TS:XFINE", name="motorX")
    motor_x: ControlEnum = Cpt(ControlEnum, "TS:XFINE")

    motor_y = Motor(prefix="BL20J-OP-PCHRO-01:TS:YFINE", name="motorY")

    def set(self, position: str) -> AsyncStatus:
        task: asyncio.Task = yield {}
        c: AsyncStatus = AsyncStatus(awaitable=task)
        return c
        # status = self.motor_x.set(position)
        # return status
