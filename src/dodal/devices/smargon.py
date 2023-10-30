from asyncio import wait_for
from enum import Enum
from typing import Iterator, Optional, Tuple

import numpy as np
from ophyd_async.core import AsyncStatus, Device
from ophyd_async.epics.motion.motor import Motor
from ophyd_async.epics.signal import epics_signal_r

from dodal.devices.ophyd_async_utils import SetProcWhenEnabledSignal


class StubPosition(Enum):
    CURRENT_AS_CENTER = 0
    RESEET_TO_ROBOT_LOAD = 1


class StubOffsets(Device):
    """Stub offsets are used to change the internal co-ordinate system of the smargon by
    adding an offset to x, y, z.
    This is useful as the smargon's centre of rotation is around (0, 0, 0). As such
    changing stub offsets will change the centre of rotation.
    In practice we don't need to change them manually, instead there are helper PVs to
    set them so that the current position is zero or to pre-defined positions.
    """

    def __init__(self, prefix: str) -> None:
        self.center_at_current_position = SetProcWhenEnabledSignal(f"{prefix}CENTER_CS")
        self.to_robot_load = SetProcWhenEnabledSignal(f"{prefix}SET_STUBS_TO_RL")
        super().__init__()

    def set(
        self, new_position: StubPosition, timeout: Optional[float] = None
    ) -> AsyncStatus:
        if new_position == StubPosition.CURRENT_AS_CENTER:
            return self.center_at_current_position.set(1)
        elif new_position == StubPosition.RESEET_TO_ROBOT_LOAD:
            return self.to_robot_load.set(1)


class XYZLimitsChecker(Device):
    """Checks that a position is within the XYZ limits of the motor.
    To use set the x, y, z vector to the device and read check `within_limits`
    """

    def __init__(self, prefix: str) -> None:
        self.within_limits = False

        axes = ["X", "Y", "Z"]
        self.limit_signals = {
            axis: (
                epics_signal_r(float, f"{prefix}{axis}.LLM"),
                epics_signal_r(float, f"{prefix}{axis}.HLM"),
            )
            for axis in axes
        }

    def children(self) -> Iterator[Tuple[str, Device]]:
        for attr, signals in self.limit_signals.items():
            yield attr + "low_lim", signals[0]
            yield attr + "high_lim", signals[1]
        return super().children()

    async def _check_limits(self, position: np.ndarray):
        check_within_limits = True
        for i, axis_limits in enumerate(self.limit_signals.values()):
            check_within_limits &= (
                (await axis_limits[0].get_value())
                < position[i]
                < (await axis_limits[1].get_value())
            )
        self.within_limits = check_within_limits

    def set(self, position: np.ndarray) -> AsyncStatus:
        return AsyncStatus(wait_for(self._check_limits(position), None))


class Smargon(Device):
    """
    Real motors added to allow stops following pin load (e.g. real_x1.stop() )
    X1 and X2 real motors provide compound chi motion as well as the compound X travel,
    increasing the gap between x1 and x2 changes chi, moving together changes virtual x.
    Robot loading can nudge these and lead to errors.
    """

    def __init__(self, prefix: str, name: str) -> None:
        self.prefix = prefix

        self.x = Motor(f"{prefix}X")
        self.x_low_lim = epics_signal_r(float, f"{prefix}X.LLM")
        self.x_high_lim = epics_signal_r(float, f"{prefix}X.HLM")

        self.y = Motor(f"{prefix}Y")
        self.z = Motor(f"{prefix}Z")

        self.chi = Motor(f"{prefix}CHI")
        self.phi = Motor(f"{prefix}PHI")
        self.omega = Motor(f"{prefix}OMEGA")

        self.real_x1 = Motor(f"{prefix}MOTOR_3")
        self.real_x2 = Motor(f"{prefix}MOTOR_4")
        self.real_y = Motor(f"{prefix}MOTOR_1")
        self.real_z = Motor(f"{prefix}MOTOR_2")
        self.real_phi = Motor(f"{prefix}MOTOR_5")
        self.real_chi = Motor(f"{prefix}MOTOR_6")

        self.stub_offsets = StubOffsets(prefix)
        self.limit_checker = XYZLimitsChecker(prefix)
        super().__init__(name)
