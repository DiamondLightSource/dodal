"""Handy test constants, that this module will use for parametrized testing."""

from math import (
    cos as cosine_function,
)
from math import (
    pi,
)
from math import (
    sin as sine_function,
)
from typing import Any, Final

INVALID_ENERGY_UNITS: Final[tuple[Any, ...]] = (
    "",
    "*^&",
    16,
    cosine_function,
    KeyError(),
    object(),
    "-9",
    -9.0,
    pi,
    True,
    False,
)

NON_NUMERICALS: Final[tuple[Any, ...]] = (
    sine_function,
    object(),
    ValueError(),
    "312",
    "*$",
    "",
    " ",
    "Hello World",
    "7.6",
    True,
    False,
)

UNSUPPORTED_ENERGY_UNITS: Final[tuple[str, ...]] = (
    "meV",
    "KILOelectronvolts",
    "kev",
    "k_eV",
    "MeV",
    "PeV",
    "J",
    "Joules",
    "s",
    "GHz",
)
