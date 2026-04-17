from collections.abc import Iterable
from dataclasses import dataclass
from typing import Self

import numpy as np
from ophyd_async.core import (
    Array1D,
)


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
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)
    rotation_matrix = np.array(
        [
            [cos_theta, sin_theta],
            [-sin_theta, cos_theta],
        ]
    )
    return do_rotation(x, y, rotation_matrix)


def rotate_counter_clockwise(theta: float, x: float, y: float) -> tuple[float, float]:
    return rotate_clockwise(-theta, x, y)


MotorOffsetAndPhase = Array1D[np.float32]


@dataclass
class AngleWithPhase:
    """Represents a point in an absolute rotational space which is defined by a phase where 0<=phase<360
     and an offset from an origin where the absolute coordinate is the sum of the phase and the offset.

    Attributes:
        offset: The offset of 0 phase from some other unwrapped rotational coordinate space
        phase: The phase in degrees relative to this offset.
    """

    offset: float
    phase: float = 0.0

    def __post_init__(self) -> None:
        correction = 360 * (self.phase // 360)
        self.offset += correction
        self.phase -= correction

    @classmethod
    def from_iterable(cls, values: Iterable[float]) -> Self:
        """Construct a normalised representation of the offset and phase, such that
        0 <= phase < 360.

        Args:
            values (Iterable[float]): the offset and phase as a list or other iterable
        """
        offset, phase = values
        return cls(offset, phase)

    @classmethod
    def wrap(cls, unwrapped: float) -> "AngleWithPhase":
        """Construct a representation such that offset = n * 360 and 0 <= phase < 360.

        Args:
             unwrapped (float): The unwrapped angle in degrees
        """
        offset = AngleWithPhase.offset_from_unwrapped(unwrapped)
        return cls(offset, unwrapped - offset)

    def rebase_to(self, other: Self) -> "AngleWithPhase":
        """Return this angle with the offset adjusted such that the phases can be compared."""
        correction = other.offset - self.offset
        if correction % 360:
            return AngleWithPhase([self.offset + correction, self.phase - correction])
        else:
            return self

    def unwrap(self) -> float:
        """Generate the unwrapped representation of this angle."""
        return self.offset + self.phase

    def phase_distance(self, phase: float) -> float:
        """Determine the shortest distance between this angle and the specified phase.

        Args:
            phase (float): The phase angle to compare to
        """
        phase = phase % 360
        max_theta = max(self.phase, phase)
        min_theta = min(self.phase, phase)
        return min(max_theta - min_theta, min_theta + 360 - max_theta)

    @classmethod
    def offset_from_unwrapped(cls, unwrapped_deg: float) -> float:
        """Obtain the offset from the corresponding wrapped angle in degrees."""
        return round(unwrapped_deg // 360) * 360

    def nearest_with_phase(self, phase_deg: float) -> "AngleWithPhase":
        """Return the nearest angle to this one with the specified phase."""
        phase_deg = phase_deg % 360
        if phase_deg > self.phase:
            return (
                AngleWithPhase(self.offset, phase_deg)
                if phase_deg - self.phase <= 180
                else AngleWithPhase(self.offset - 360, phase_deg)
            )
        else:
            return (
                AngleWithPhase(self.offset, phase_deg)
                if self.phase - phase_deg <= 180
                else AngleWithPhase(self.offset + 360, phase_deg)
            )


def reflect_phase(phase) -> float:
    """Convert the phase angle as if the corresponding unwrapped angle were to
    be reflected about the origin and then re-wrapped, this corresponds to
    converting a clockwise angle to an anti-clockwise angle and vice-versa.
    """
    return (360 - phase) % 360
