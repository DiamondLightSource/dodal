import math

canonical_barnett_conversion = -1.0e3
reverse_barnett_conversion = -1.0e-3


def attenuation_from_natural_log_of_transmission(ln_t: float):
    return canonical_barnett_conversion * ln_t


def attenuation_from_transmission(transmission_as_fraction: float):
    ln_t = math.log(transmission_as_fraction)
    return attenuation_from_natural_log_of_transmission(ln_t)


def natural_log_of_transmission_from_attenuation(attenuation_bn: float):
    return reverse_barnett_conversion * attenuation_bn


def transmission_from_attenutation(attenuation_bn: float):
    ln_t = natural_log_of_transmission_from_attenuation(attenuation_bn)
    return math.exp(ln_t)
