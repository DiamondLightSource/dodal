from typing import Annotated

from pydantic import (
    Field,
    StrictFloat,
    validate_call,
)

from dodal.common.general_maths.transmission_interconversion import (
    attenuation_from_natural_log_of_transmission,
    natural_log_of_transmission_from_attenuation,
)


@validate_call
def photon_mass_attenuation_per_unit_length(
    energy_kev: StrictFloat,
    photon_absorption_factor_per_unit_length: Annotated[StrictFloat, Field(ge=0)],
    energy_dependence_exponent: Annotated[StrictFloat, Field(le=0)],
) -> float:
    """Calculates mass attenuation per unit length.

    Args:
        energy_kev (StrictFloat): energy
        photon_absorption_factor_per_unit_length(StrictFloat greater than/equal to 0): p
        hoton absorption factor per unit length
        energy_dependence_exponent (StrictFloat less than/equal to 0): energy
        dependence exponent

    Returns:
        (float): mass attenuation per unit length.
    """
    return photon_absorption_factor_per_unit_length * (
        energy_kev**energy_dependence_exponent
    )


@validate_call
def attenuation_at_depth_cm(
    depth_cm: Annotated[StrictFloat, Field(ge=0)],
    absorption_coefficient_per_cm: Annotated[StrictFloat, Field(ge=0)],
) -> float:
    """Calculates attenuation in Barnett units, where 1000 Bn equivalent to 1/e,
    0Bn to 1 and 2000 Bn to 1/(e^2).

    Args:
        depth_cm (StrictFloat greater than/equal to 0):  depth of absorption
        absorption_coefficient_per_cm (StrictFloat greater than/equal to 0): absorption
        coefficient per cm

    Raises:
        ValueError: If either depth_cm or absorption_coefficient are negative, an error
        is raised

    Returns:
        (float): attenuation in Barnett units
    """
    ln_t = -(depth_cm * absorption_coefficient_per_cm)
    return attenuation_from_natural_log_of_transmission(ln_t)


@validate_call
def thickness_cm_required_to_attenuate(
    target_attenuation_bn: Annotated[StrictFloat, Field(ge=0)],
    absorption_coefficient_per_cm: Annotated[StrictFloat, Field(ge=1.0e-14)],
) -> float:
    """Calculates material depth in cm.

    Args:
        target_attenuation_bn (StrictFloat greater than/equal to 0): Target attenuation
        to meet in Barnett attenuation units.
        absorption_coefficient_per_cm (StrictFloat greater than/equal to 0):  absorption
        coefficient per cm


    Raises:
        ValueError: if attenuation is below zero, or absorption is below the minimum
        meaningful absorption coefficient, a value error is raised

    Returns:
        (float): material depth in cm.
    """
    ln_target_t = natural_log_of_transmission_from_attenuation(target_attenuation_bn)
    return -(ln_target_t / absorption_coefficient_per_cm)
