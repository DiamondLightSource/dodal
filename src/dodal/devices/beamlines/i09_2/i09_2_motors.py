import asyncio

from bluesky.protocols import (
    Locatable,
    Location,
    Movable,
    Reading,
    Stoppable,
    Subscribable,
)
from ophyd_async.core import (
    Callback,
    StandardReadable,
    StandardReadableFormat,
    WatchableAsyncStatus,
    WatcherUpdate,
    observe_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_w
from ophyd_async.epics.motor import Motor


class PiezoElectricMotor(
    StandardReadable, Stoppable, Locatable[float], Subscribable[float], Movable[float]
):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.user_readback = epics_signal_r(float, prefix + ":POS:RD")

        self.user_setpoint = epics_signal_rw(float, prefix + ":MOV:RD")
        self.motor_stop = epics_signal_w(int, prefix + ":HLT:WR.PROC")

        # Whether set() should complete successfully or not
        self._set_success = True

        super().__init__(name)

    def set_name(self, name: str, *, child_name_separator: str | None = None) -> None:
        """Set name of the motor and its children."""
        super().set_name(name, child_name_separator=child_name_separator)
        # Readback should be named the same as its parent in read()
        self.user_readback.set_name(name)

    async def stop(self, success=False):
        """Request to stop moving and return immediately."""
        self._set_success = success
        # Put with completion will never complete as we are waiting for completion on
        # the move above, so need to pass wait=False
        await self.motor_stop.set(1, wait=False)

    async def locate(self) -> Location[float]:
        """Return the current setpoint and readback of the motor."""
        setpoint, readback = await asyncio.gather(
            self.user_setpoint.get_value(), self.user_readback.get_value()
        )
        return Location(setpoint=setpoint, readback=readback)

    def subscribe_reading(self, function: Callback[dict[str, Reading[float]]]) -> None:
        """Subscribe to reading."""
        self.user_readback.subscribe_reading(function)

    subscribe = subscribe_reading

    def clear_sub(self, function: Callback[dict[str, Reading[float]]]) -> None:
        """Unsubscribe."""
        self.user_readback.clear_sub(function)

    @WatchableAsyncStatus.wrap
    async def set(self, new_position: float):
        """Move motor to the given value."""
        self._set_success = True

        old_position = await self.user_setpoint.get_value()
        move_status = self.user_setpoint.set(new_position, wait=True)
        async for current_position in observe_value(
            self.user_readback, done_status=move_status
        ):
            yield WatcherUpdate(
                current=current_position,
                initial=old_position,
                target=new_position,
                name=self.name,
            )
        if not self._set_success:
            raise RuntimeError("Motor was stopped")


class I092SampleManipulator(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.x1 = PiezoElectricMotor(prefix + "X1")
            self.x2 = PiezoElectricMotor(prefix + "X2")
            self.x3 = PiezoElectricMotor(prefix + "X3")
            self.y = PiezoElectricMotor(prefix + "Y")
            self.z1 = PiezoElectricMotor(prefix + "Z1")
            self.z2 = PiezoElectricMotor(prefix + "Z2")

            self.xc = Motor(prefix + "X")
            self.zc = Motor(prefix + "Z")

        super().__init__(name)
