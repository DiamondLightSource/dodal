import numpy as np


def step_to_num(start: float, stop: float, step: float) -> tuple[float, float, int]:
    """
    Standard handling for converting from start, stop, step to start, stop, num
    Forces step to be same direction as length
    Includes a final point if it is within 1% of the final step, prevents floating
    point arithmatic errors from giving inconsistent shaped scans between steps of an
    outer axis.

    Args:
        start (float):
            Start of length, will be returned unchanged
        stop (float):
            End of length, if length/step does not divide cleanly will be returned
            extended up to 1% of step, or else truncated.
        step (float):
            Length of a step along the line formed from start to stop.
            If stop < start, will be coerced to be backwards.

    Returns:
        start, adjusted_stop, num = Tuple[float, float, int]
        start will be returned unchanged
        adjusted_stop = start + (num - 1) * step
        num is the maximal number of steps that could fit into the length.

    """
    # Make step be the right direction
    step = abs(step) if stop >= start else -abs(step)
    # If stop is within 1% of a step then include it
    steps = int((stop - start) / step + 0.01)
    return start, start + steps * step, steps + 1  # include 1st point


def in_micros(t: float) -> int:
    """
    Converts between a positive number of seconds and an equivalent
    number of microseconds.

    Args:
        t (float): A time in seconds
    Raises:
        ValueError: if t < 0
    Returns:
        t (int): A time in microseconds, rounded up to the nearest whole microsecond,
    """
    if t < 0:
        raise ValueError(f"Expected a positive time in seconds, got {t!r}")
    return int(np.ceil(t * 1e6))


class Rectangle2D:
    """
    A 2D rectangle defined by two opposite corners.

    This class represents a rectangle in 2D space using two points: (x1, y1) and (x2, y2).
    It provides methods to query rectangle properties and check point containment.

    Attributes:
        x1 (float): The x-coordinate of the first corner.
        y1 (float): The y-coordinate of the first corner.
        x2 (float): The x-coordinate of the second corner.
        y2 (float): The y-coordinate of the second corner.
    """

    def __init__(self, x1: float, y1: float, x2: float, y2: float):
        """
        Initialize a Rectangle2D with two corner points.

        Args:
            x1 (float): The x-coordinate of the first corner.
            y1 (float): The y-coordinate of the first corner.
            x2 (float): The x-coordinate of the second corner.
            y2 (float): The y-coordinate of the second corner.
        """
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2

    def get_max_x(self) -> float:
        """
        Get the maximum x-coordinate of the rectangle.

        Returns:
            float: The larger of the two x-coordinates (x1, x2).
        """
        return max(self.x1, self.x2)

    def get_min_x(self) -> float:
        """
        Get the minimum x-coordinate of the rectangle.

        Returns:
            float: The smaller of the two x-coordinates (x1, x2).
        """
        return min(self.x1, self.x2)

    def get_max_y(self) -> float:
        """
        Get the maximum y-coordinate of the rectangle.

        Returns:
            float: The larger of the two y-coordinates (y1, y2).
        """
        return max(self.y1, self.y2)

    def get_min_y(self) -> float:
        """
        Get the minimum y-coordinate of the rectangle.

        Returns:
            float: The smaller of the two y-coordinates (y1, y2).
        """
        return min(self.y1, self.y2)

    def contains(self, x: float, y: float) -> bool:
        """
        Check if a point is contained within the rectangle.

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
