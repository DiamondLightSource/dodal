"""
All the public methods in this module return a lookup table of some kind that
converts the source value s to a target value t for different values of s.
"""

from collections.abc import Callable, Sequence
from io import StringIO

import aiofiles
import numpy as np
from numpy import interp, loadtxt

from dodal.log import LOGGER


async def energy_distance_table(lookup_table_path: str) -> np.ndarray:
    """
    Returns a numpy formatted lookup table for required positions of an ID gap to
    provide emission at a given beam energy.

    Args:
        lookup_table_path: Path to lookup table

    Returns:
        ndarray: Lookup table
    """

    # Slight cheat to make the file IO async, numpy doesn't do any real IO now, just
    # decodes the text
    async with aiofiles.open(lookup_table_path) as stream:
        raw_table = await stream.read()
    return loadtxt(StringIO(raw_table), comments=["#", "Units"])


def parse_lookup_table(filename: str) -> list[Sequence]:
    """Parse a generic lookup table with a number of columns >= 2 and return a list \
        in column major order of the values in it."""
    LOGGER.info(f"Parsing lookup table file {filename}")

    lut_vals = zip(*loadtxt(filename, comments=["#", "Units"]), strict=False)
    return list(lut_vals)


def linear_interpolation_lut(
    s_values: Sequence, t_values: Sequence
) -> Callable[[float], float]:
    """Returns a callable that converts values by linear interpolation of lookup table
    values.

    If the value falls outside the lookup table then the closest value will be used."""
    # numpy interp expects x-values to be increasing
    if not np.all(np.diff(s_values) > 0):
        LOGGER.info(
            "Configuration values in the lookup table are not ascending, trying reverse order..."
        )
        s_values = list(reversed(s_values))
        t_values = list(reversed(t_values))
        if not np.all(np.diff(s_values) > 0):
            raise AssertionError(
                "Configuration lookup table does not monotonically increase or decrease."
            )

    def s_to_t2(s: float) -> float:
        return float(interp(s, s_values, t_values))

    return s_to_t2


def linear_extrapolation_lut(
    s_values: Sequence[float], t_values: Sequence[float]
) -> Callable[[float], float]:
    """
    Return a callable that implements f(s) = t according to the conversion table data
    supplied, with linear extrapolation outside that range. Inside the range of the table,
    the function is equivalent to that returned by linear_interpolation_lut

    Args:
        s_values:  Values of the independent axis
        t_values:  Values of the dependent axis

    Returns:
        A callable that returns t for the given s
    """
    assert len(s_values) == len(t_values), (
        "Lookup table does not have the same number of values for each axis"
    )
    assert len(s_values) > 1, "Need at least 2 points in the lookup table"
    interp = linear_interpolation_lut(s_values, t_values)
    s_min = s_values[0]
    s_max = s_values[-1]

    def s_to_t(s: float) -> float:
        if s < s_min:
            return t_values[0] + (s - s_min) * (t_values[1] - t_values[0]) / (
                s_values[1] - s_values[0]
            )
        elif s > s_max:
            return t_values[-1] + (s - s_max) * (t_values[-1] - t_values[-2]) / (
                s_values[-1] - s_values[-2]
            )
        else:
            return interp(s)

    return s_to_t
