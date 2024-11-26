from collections.abc import Collection, Generator
from dataclasses import dataclass
from enum import Enum
from math import isclose
from typing import cast

from bluesky import plan_stubs as bps
from bluesky.utils import Msg
from ophyd_async.core import AsyncStatus, Device, StandardReadable, wait_for_value
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.epics.motor import Motor

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

    def __init__(self, name: str = "", prefix: str = ""):
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


@dataclass
class AxisLimit:
    """Represents the minimum and maximum allowable values on an axis"""

    min_value: float
    max_value: float

    def contains(self, pos: float):
        """Determine if the specified value is within limits.

        Args:
            pos: the value to check

        Returns:
            True if the value does not exceed the limits
        """
        return self.min_value <= pos <= self.max_value


@dataclass
class XYZLimits:
    """The limits of the smargon x, y, z axes."""

    x: AxisLimit
    y: AxisLimit
    z: AxisLimit

    def position_valid(self, pos: Collection[float]) -> bool:
        return all(
            axis_limits.contains(value)
            for axis_limits, value in zip([self.x, self.y, self.z], pos, strict=False)
        )


class Smargon(StandardReadable):
    """
    Real motors added to allow stops following pin load (e.g. real_x1.stop() )
    X1 and X2 real motors provide compound chi motion as well as the compound X travel,
    increasing the gap between x1 and x2 changes chi, moving together changes virtual x.
    Robot loading can nudge these and lead to errors.
    """

    def __init__(self, prefix: str = "", name: str = ""):
        with self.add_children_as_readables():
            self.x = Motor(prefix + "X")
            self.y = Motor(prefix + "Y")
            self.z = Motor(prefix + "Z")
            self.chi = Motor(prefix + "CHI")
            self.phi = Motor(prefix + "PHI")
            self.omega = Motor(prefix + "OMEGA")
            self.real_x1 = Motor(prefix + "MOTOR_3")
            self.real_x2 = Motor(prefix + "MOTOR_4")
            self.real_y = Motor(prefix + "MOTOR_1")
            self.real_z = Motor(prefix + "MOTOR_2")
            self.real_phi = Motor(prefix + "MOTOR_5")
            self.real_chi = Motor(prefix + "MOTOR_6")
            self.stub_offsets = StubOffsets(prefix=prefix)
            self.disabled = epics_signal_r(int, prefix + "DISABLED")

        super().__init__(name)

    def get_xyz_limits(self) -> Generator[Msg, None, XYZLimits]:
        """Obtain a plan stub that returns the smargon XYZ axis limits

        Yields:
            Bluesky messages

        Returns:
            the axis limits
        """
        limits = {}
        for name, pv in [
            (attr_name, getattr(self, attr_name)) for attr_name in ["x", "y", "z"]
        ]:
            min_value = yield from bps.rd(pv.low_limit_travel)
            max_value = yield from bps.rd(pv.high_limit_travel)
            limits[name] = AxisLimit(min_value, max_value)
        return XYZLimits(**limits)
