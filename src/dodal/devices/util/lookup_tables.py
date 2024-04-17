"""
All the public methods in this module return a lookup table of some kind that
converts the source value s to a target value t for different values of s.
"""

from collections.abc import Sequence
from typing import Callable

import numpy as np
from numpy import interp, loadtxt

from dodal.log import LOGGER


def linear_interpolation_lut(filename: str) -> Callable[[float], float]:
    """Returns a callable that converts values by linear interpolation of lookup table values"""
    LOGGER.info(f"Using lookup table {filename}")
    s_and_t_vals = zip(*loadtxt(filename, comments=["#", "Units"]))

    s_values: Sequence
    t_values: Sequence
    s_values, t_values = s_and_t_vals

    # numpy interp expects x-values to be increasing
    if not np.all(np.diff(s_values) > 0):
        LOGGER.info(
            f"Configuration file {filename} values are not ascending, trying reverse order..."
        )
        s_values = list(reversed(s_values))
        t_values = list(reversed(t_values))
        if not np.all(np.diff(s_values) > 0):
            raise AssertionError(
                f"Configuration file {filename} lookup table does not monotonically increase or decrease."
            )

    def s_to_t2(s: float) -> float:
        if s < s_values[0] or s > s_values[len(s_values) - 1]:
            raise ValueError(
                f"Lookup table does not support extrapolation from file {filename}, s={s}"
            )
        return float(interp(s, s_values, t_values))

    return s_to_t2
