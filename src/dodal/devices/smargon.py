import asyncio
from enum import Enum
from math import isclose
from typing import TypedDict, cast

from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    Device,
    StrictEnum,
    derived_signal_r,
    set_and_wait_for_value,
    wait_for_value,
)
from ophyd_async.epics.core import (
    CALCULATE_TIMEOUT,
    CalculatableTimeout,
    WatchableAsyncStatus,
    epics_signal_r,
    epics_signal_rw,
)
from ophyd_async.epics.motor import Motor

from dodal.devices.motors import XYZOmegaStage
from dodal.devices.util.epics_util import SetWhenEnabled


class StubPosition(Enum):
    CURRENT_AS_CENTER = 0
    RESET_TO_ROBOT_LOAD = 1


def approx_equal_to(target, deadband: float = 1e-9):
    def approx_equal_to_target(value):
        return isclose(target, value, rel_tol=0, abs_tol=deadband)

    return approx_equal_to_target


class StubOffsets(Device):
    """Stub offsets are used to change the internal co-ordinate system of the smargon by
    adding an offset to x, y, z.
    This is useful as the smargon's centre of rotation is around (0, 0, 0). As such
    changing stub offsets will change the centre of rotation.
    In practice we don't need to change them manually, instead there are helper PVs to
    set them so that the current position is zero or to pre-defined positions.
    """

    def __init__(self, prefix: str, name: str = ""):
        self.center_at_current_position = SetWhenEnabled(prefix=prefix + "CENTER_CS")
        self.to_robot_load = SetWhenEnabled(prefix=prefix + "SET_STUBS_TO_RL")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: StubPosition):
        if value == StubPosition.CURRENT_AS_CENTER:
            await self.center_at_current_position.set(1)
            smargon = cast(Smargon, self.parent)
            await wait_for_value(
                smargon.x.user_readback, approx_equal_to(0.0, 0.1), None
            )
            await wait_for_value(
                smargon.y.user_readback, approx_equal_to(0.0, 0.1), None
            )
            await wait_for_value(
                smargon.z.user_readback, approx_equal_to(0.0, 0.1), None
            )
        else:
            await self.to_robot_load.set(1)


class DeferMoves(StrictEnum):
    ON = "Defer On"
    OFF = "Defer Off"


class CombinedMove(TypedDict, total=False):
    """A move on multiple axes at once using a deferred move."""

    x: float | None
    y: float | None
    z: float | None
    omega: float | None
    phi: float | None
    chi: float | None


class Mod360Motor(Motor):
    def __init__(self, prefix: str, name="") -> None:
        super().__init__(name)
        self._raw_readback = epics_signal_r(float, prefix + ".RBV")
        self.user_readback = derived_signal_r(
            self._mod_360, raw_readback=self._raw_readback
        )

    def _mod_360(self, raw_readback: float) -> float:
        return raw_readback % 360

    def _nearest_360(self):
        return round(await self.user_readback.get_value() / 360) * 360

    @WatchableAsyncStatus.wrap
    async def set(
        self, new_position: float, timeout: CalculatableTimeout = CALCULATE_TIMEOUT
    ):
        return super().set(self._nearest_360 + new_position, timeout)


class Smargon(XYZOmegaStage, Movable):
    """Real motors added to allow stops following pin load (e.g. real_x1.stop() )
    X1 and X2 real motors provide compound chi motion as well as the compound X travel,
    increasing the gap between x1 and x2 changes chi, moving together changes virtual x.
    Robot loading can nudge these and lead to errors.
    """

    DEFERRED_MOVE_SET_TIMEOUT = 5

    def __init__(self, prefix: str, name: str = ""):
        with self.add_children_as_readables():
            self.omega = Mod360Motor(prefix + "OMEGA")
            self.chi = Motor(prefix + "CHI")
            self.phi = Motor(prefix + "PHI")
            self.real_x1 = Motor(prefix + "MOTOR_3")
            self.real_x2 = Motor(prefix + "MOTOR_4")
            self.real_y = Motor(prefix + "MOTOR_1")
            self.real_z = Motor(prefix + "MOTOR_2")
            self.real_phi = Motor(prefix + "MOTOR_5")
            self.real_chi = Motor(prefix + "MOTOR_6")
            self.stub_offsets = StubOffsets(prefix=prefix)
            self.disabled = epics_signal_r(int, prefix + "DISABLED")

        self.defer_move = epics_signal_rw(DeferMoves, prefix + "CS1:DeferMoves")

        super().__init__(prefix, name)

    @AsyncStatus.wrap
    async def set(self, value: CombinedMove):
        """This will move all motion together in a deferred move.

        Once defer_move is on, sets to any axis do not immediately move the axis. Instead
        the setpoint will go to that value. Then, when defer_move is switched off all
        axes will move at the same time. The put callbacks on the axes themselves will
        only come back after the motion on that axis finished.
        """
        await self.defer_move.set(DeferMoves.ON)
        try:
            finished_moving = []
            for motor_name, new_setpoint in value.items():
                if new_setpoint is not None and isinstance(new_setpoint, int | float):
                    axis: Motor = getattr(self, motor_name)
                    await axis.check_motor_limit(
                        await axis.user_setpoint.get_value(), new_setpoint
                    )
                    put_completion = await set_and_wait_for_value(
                        axis.user_setpoint,
                        new_setpoint,
                        timeout=self.DEFERRED_MOVE_SET_TIMEOUT,
                        wait_for_set_completion=False,
                    )
                    finished_moving.append(put_completion)
        finally:
            await self.defer_move.set(DeferMoves.OFF)
        await asyncio.gather(*finished_moving)
