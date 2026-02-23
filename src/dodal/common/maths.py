from typing import NamedTuple, Self

import numpy as np
from ophyd_async.core import (
    Array1D,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_rw,
)
from ophyd_async.epics.motor import Motor


def step_to_num(start: float, stop: float, step: float) -> tuple[float, float, int]:
    """Standard handling for converting from start, stop, step to start, stop, num.
    Forces step to be same direction as length.
    Includes a final point if it is within 1% of the final step, prevents floating
    point arithmatic errors from giving inconsistent shaped scans between steps of an
    outer axis.

    Args:
        start (float): Start of length, will be returned unchanged.
        stop (float): End of length, if length/step does not divide cleanly will be
            returned extended up to 1% of step, or else truncated.
        step (float): Length of a step along the line formed from start to stop. If
            stop < start, will be coerced to be backwards.

    Returns:
        start, adjusted_stop, num = Tuple[float, float, int]
            - start will be returned unchanged.
            - adjusted_stop = start + (num - 1) * step.
            - num is the maximal number of steps that could fit into the length.

    """
    # Make step be the right direction
    step = abs(step) if stop >= start else -abs(step)
    # If stop is within 1% of a step then include it
    steps = int((stop - start) / step + 0.01)
    return start, start + steps * step, steps + 1  # include 1st point


def in_micros(t: float) -> int:
    """Converts between a positive number of seconds and an equivalent
    number of microseconds.

    Args:
        t (float): A time in seconds.

    Raises:
        ValueError: if t < 0.

    Returns:
        int: A time in microseconds, rounded up to the nearest whole microsecond.
    """
    if t < 0:
        raise ValueError(f"Expected a positive time in seconds, got {t!r}")
    return int(np.ceil(t * 1e6))


class Rectangle2D:
    """A 2D rectangle defined by two opposite corners.

    This class represents a rectangle in 2D space using two points: (x1, y1) and (x2, y2).
    It provides methods to query rectangle properties and check point containment.

    Attributes:
        x1 (float): The x-coordinate of the first corner.
        y1 (float): The y-coordinate of the first corner.
        x2 (float): The x-coordinate of the second corner.
        y2 (float): The y-coordinate of the second corner.

    Args:
        x1 (float): The x-coordinate of the first corner.
        y1 (float): The y-coordinate of the first corner.
        x2 (float): The x-coordinate of the second corner.
        y2 (float): The y-coordinate of the second corner.
    """

    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2

    def get_max_x(self) -> float:
        """Get the maximum x-coordinate of the rectangle.

        Returns:
            float: The larger of the two x-coordinates (x1, x2).
        """
        return max(self.x1, self.x2)

    def get_min_x(self) -> float:
        """Get the minimum x-coordinate of the rectangle.

        Returns:
            float: The smaller of the two x-coordinates (x1, x2).
        """
        return min(self.x1, self.x2)

    def get_max_y(self) -> float:
        """Get the maximum y-coordinate of the rectangle.

        Returns:
            float: The larger of the two y-coordinates (y1, y2).
        """
        return max(self.y1, self.y2)

    def get_min_y(self) -> float:
        """Get the minimum y-coordinate of the rectangle.

        Returns:
            float: The smaller of the two y-coordinates (y1, y2).
        """
        return min(self.y1, self.y2)

    def contains(self, x: float, y: float) -> bool:
        """Check if a point is contained within the rectangle.

        Args:
            x (float): The x-coordinate of the point.
            y (float): The y-coordinate of the point.

        Returns:
            bool: True if the point is within the rectangle bounds, False otherwise.
        """
        return (
            self.get_min_x() <= x <= self.get_max_x()
            and self.get_min_y() <= y <= self.get_max_y()
        )


"""
| Rotation | Formula for X_rot | Formula for Y_rot |
| -------- | ----------------- | ----------------- |
| CW       | x cosθ + y sinθ   | -x sinθ + y cosθ  |
| CCW      | x cosθ - y sinθ   | x sinθ + y cosθ   |
"""


def do_rotation(x: float, y: float, rotation_matrix: np.ndarray) -> tuple[float, float]:
    positions = np.array([x, y])
    rotation = rotation_matrix @ positions
    return float(rotation[0]), float(rotation[1])


def rotate_clockwise(theta: float, x: float, y: float) -> tuple[float, float]:
    rotation_matrix = np.array(
        [
            [np.cos(theta), np.sin(theta)],
            [-np.sin(theta), np.cos(theta)],
        ]
    )
    return do_rotation(x, y, rotation_matrix)


def rotate_counter_clockwise(theta: float, x: float, y: float) -> tuple[float, float]:
    return rotate_clockwise(-theta, x, y)


MotorOffsetAndPhase = Array1D[np.float32]


class AngleWithPhase(NamedTuple):
    """Represents a point in rotational space which has 0<=phase<360 and
    offset = n * 360.
    """

    offset: float
    phase: float

    @classmethod
    def from_offset_and_phase(
        cls, offset_and_phase: MotorOffsetAndPhase
    ) -> "AngleWithPhase":
        return cls(offset_and_phase[0], offset_and_phase[1])

    @classmethod
    def wrap(cls, unwrapped: float) -> "AngleWithPhase":
        offset = AngleWithPhase.offset_from_unwrapped(unwrapped)
        return cls(offset, unwrapped - offset)

    def unwrap(self) -> float:
        return self.offset + self.phase

    def phase_distance(self, other: Self) -> float:
        max_theta = max(self.phase, other.phase)
        min_theta = min(self.phase, other.phase)
        return min(max_theta - min_theta, min_theta + 360 - max_theta)

    @classmethod
    def offset_from_unwrapped(cls, unwrapped_deg: float) -> float:
        """Obtain the offset from the corresponding wrapped angle in degrees."""
        return round(unwrapped_deg // 360) * 360

    def project_to_unwrapped(self, phase_deg: float) -> float:
        """Return the supplied phase angle projected into the unwrapped space defined by our offset."""
        return self.offset + phase_deg


class RotationalAxis(StandardReadable):
    def __init__(self, real_motor: Motor, name=""):
        self._real_motor = Reference(real_motor)
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.offset_and_phase = derived_signal_rw(
                self._get_motor_offset_and_phase,
                self._set_motor_offset_and_phase,
                motor_pos=real_motor,
            )
        with self.add_children_as_readables():
            self.phase = derived_signal_rw(
                self._get_phase, self._set_phase, offset_and_phase=self.offset_and_phase
            )
        super().__init__(name=name)

    def _get_motor_offset_and_phase(self, motor_pos: float) -> MotorOffsetAndPhase:
        angle = AngleWithPhase.wrap(motor_pos)
        return np.array([angle.offset, angle.phase])

    async def _set_motor_offset_and_phase(self, value: MotorOffsetAndPhase):
        await self._real_motor().set(
            AngleWithPhase.from_offset_and_phase(value).unwrap()
        )

    def _get_phase(self, offset_and_phase: MotorOffsetAndPhase) -> float:
        return offset_and_phase[1].item()

    async def _set_phase(self, value: float) -> None:
        """Set the motor phase to the specified phase value in degrees.
        The motor will travel via the shortest distance path.
        """
        pass

    def distance(self, theta1_deg: float, theta2_deg: float) -> float:
        """Obtain the shortest distance between theta2 and theta1 in degrees.
        If the axis is wrapped, this will be the shortest distance in mod360 space (i.e. always <= 180 degrees).
        If the axis is unwrapped, this will be the distance in absolute (unwrapped) space.
        """
        pass

    def get_wrapped_origin(self, unwrapped_deg: float) -> AngleWithPhase:
        """Obtain an origin in wrapped space that can be used to project phase angles into unwrapped space."""
        pass


class WrappedAxis(RotationalAxis):
    def distance(self, theta1_deg: float, theta2_deg: float) -> float:
        return AngleWithPhase.wrap(theta1_deg).phase_distance(
            AngleWithPhase.wrap(theta2_deg)
        )

    def get_wrapped_origin(self, unwrapped_deg: float) -> AngleWithPhase:
        return AngleWithPhase(AngleWithPhase.offset_from_unwrapped(unwrapped_deg), 0)

    async def _set_phase(self, value: float):
        offset_and_phase = await self.offset_and_phase.get_value()
        current_position = AngleWithPhase.from_offset_and_phase(offset_and_phase)
        target_value = value + current_position.offset
        while target_value - current_position.unwrap() >= 180:
            target_value -= 360
        else:
            while target_value - current_position.unwrap() <= -180:
                target_value += 360

        await self._real_motor().set(target_value)
