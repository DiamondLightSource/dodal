import math

CANONICAL_BARNETT_CONVERSION = -1.0e3
REVERSE_BARNETT_CONVERSION = -1.0e-3


def attenuation_from_natural_log_of_transmission(ln_t: float) -> float:
    """Converts from natural log of transmission fraction into Barnett attenuation units
    .

    Args:
        ln_t (float): natural log of transmission fraction

    Returns:
        (float): Barnett attenuation units
    """
    return CANONICAL_BARNETT_CONVERSION * ln_t


def attenuation_from_transmission(transmission_as_fraction: float) -> float:
    """Converts from transmission fraction into Barnett attenuation units.

    Args:
        transmission_as_fraction (float): transmission fraction

    Returns:
        (float): Barnett attenuation units.
    """
    ln_t = math.log(transmission_as_fraction)
    return attenuation_from_natural_log_of_transmission(ln_t)


def natural_log_of_transmission_from_attenuation(attenuation_bn: float) -> float:
    """Converts from Barnett attenuation units into natural log of transmission fraction
    .

    Args:
        attenuation_bn (float): Barnett attenuation units

    Returns:
        (float): natural log of transmission fraction
    """
    return REVERSE_BARNETT_CONVERSION * attenuation_bn


def transmission_from_attenutation(attenuation_bn: float) -> float:
    """Converts from Barnett attenuation units into transmission fraction.

    Args:
        attenuation_bn (float): Barnett attenuation units

    Returns:
        (float): transmission fraction
    """
    ln_t = natural_log_of_transmission_from_attenuation(attenuation_bn)
    return math.exp(ln_t)
