import math
from typing import Annotated

from pydantic import Field, StrictFloat, validate_call

Attenuation_Bn = Annotated[StrictFloat, Field(ge=0.0)]

CANONICAL_NON_ABSORPTION: Attenuation_Bn = 0.0

_CANONICAL_BARNETT_CONVERSION: Attenuation_Bn = -1.0e3
_REVERSE_BARNETT_CONVERSION: float = -1.0e-3


@validate_call
def attenuation_from_natural_log_of_transmission(ln_t: StrictFloat) -> float:
    """Converts from natural log of transmission fraction into Barnett attenuation units.

    Args:
        ln_t (StrictFloat): natural log of transmission fraction

    Returns:
        (float): Barnett attenuation units
    """
    return _CANONICAL_BARNETT_CONVERSION * ln_t


@validate_call
def attenuation_from_transmission(
    transmission_as_fraction: Annotated[StrictFloat, Field(ge=0, le=1)],
) -> float:
    """Converts from transmission fraction into Barnett attenuation units.

    Args:
        transmission_as_fraction (StrictFloat): transmission fraction

    Returns:
        (float): Barnett attenuation units.
    """
    ln_t = math.log(transmission_as_fraction)
    return attenuation_from_natural_log_of_transmission(ln_t)


@validate_call
def natural_log_of_transmission_from_attenuation(
    attenuation_bn: Annotated[StrictFloat, Field(ge=0)],
) -> float:
    """Converts from Barnett attenuation units into natural log of transmission fraction.

    Args:
        attenuation_bn (StrictFloat): Barnett attenuation units - zero or a positive number

    Returns:
        (float): natural log of transmission fraction - zero or, more usually, a negative number
    """
    return _REVERSE_BARNETT_CONVERSION * attenuation_bn


@validate_call
def transmission_from_attenutation(
    attenuation_bn: Annotated[StrictFloat, Field(ge=0)],
) -> float:
    """Converts from Barnett attenuation units into transmission fraction.

    Args:
        attenuation_bn (StrictFloat): Barnett attenuation units - zero or a positive number

    Returns:
        (float): transmission fraction
    """
    ln_t = natural_log_of_transmission_from_attenuation(attenuation_bn)
    return math.exp(ln_t)
