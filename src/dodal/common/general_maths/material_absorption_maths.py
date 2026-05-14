from typing import Annotated

from pydantic import (
    BaseModel,
    Field,
    StrictFloat,
    validate_call,
)

from dodal.common.general_maths.transmission_interconversion import (
    attenuation_from_natural_log_of_transmission,
    natural_log_of_transmission_from_attenuation,
)


class ValueCheck(BaseModel):
    value: Annotated[StrictFloat, Field(ge=0)]


@validate_call
def photon_mass_attenuation_per_unit_length(
    energy_kev: StrictFloat,
    photon_absorption_factor_per_unit_length: StrictFloat,
    energy_dependence_exponent: StrictFloat,
) -> float:
    """Calculates mass attenuation per unit length.

    Args:
        energy_kev (StrictFloat): energy
        photon_absorption_factor_per_unit_length (StrictFloat): photon absorption factor
        per unit length
        energy_dependence_exponent (StrictFloat): energy dependence exponent

    Returns:
        (float): mass attenuation per unit length.
    """
    return photon_absorption_factor_per_unit_length * (
        energy_kev**energy_dependence_exponent
    )


@validate_call
def attenuation_at_depth_cm(
    depth_cm: StrictFloat, absorption_coefficient_per_cm: StrictFloat
) -> float:
    """Calculates attenuation in Barnett units, where 1000 Bn equivalent to 1/e,
    0Bn to 1 and 2000 Bn to 1/(e^2).

    Args:
        depth_cm (StrictFloat): depth of absorption
        absorption_coefficient_per_cm (StrictFloat): absorption coefficient per cm

    Raises:
        ValueError: If either depth_cm or absorption_coefficient are negative, an error
        is raised

    Returns:
        (float): attenuation in Barnett units
    """
    ValueCheck.model_validate({"value": depth_cm}, strict=True)
    ValueCheck.model_validate({"value": absorption_coefficient_per_cm}, strict=True)
    ln_t = -(depth_cm * absorption_coefficient_per_cm)
    return attenuation_from_natural_log_of_transmission(ln_t)


@validate_call
def thickness_cm_required_to_attenuate(
    target_attenuation_bn: StrictFloat,
    absorption_coefficient_per_cm: StrictFloat,
) -> float:
    """Calculates material depth in cm.

    Args:
        target_attenuation_bn (StrictFloat): Target attenuation to meet in Barnett
        attenuation units.
        absorption_coefficient_per_cm (StrictFloat): absorption coefficient per cm


    Raises:
        ValueError: if attenuation is below zero, or absorption is below the minimum
        meaningful absorption coefficient, a value error is raised

    Returns:
        (float): material depth in cm.
    """
    minimum_meaningful_absorption_coefficient = 1.0e-14
    if absorption_coefficient_per_cm < minimum_meaningful_absorption_coefficient:
        raise ValueError(
            "Invalid absorption - this calculator is not for transparent media nor thos\
                e with optical gain."
        )
    ValueCheck.model_validate({"value": target_attenuation_bn}, strict=True)
    ln_target_t = natural_log_of_transmission_from_attenuation(target_attenuation_bn)
    return -(ln_target_t / absorption_coefficient_per_cm)
