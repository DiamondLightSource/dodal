from pydantic import NonNegativeFloat, validate_call

from dodal.common.general_maths import transmission_interconversion


def photon_mass_attenuation_per_unit_length(
    energy_kev: float,
    photon_absorption_factor_per_unit_length: float,
    energy_dependence_exponent: float,
):
    """Calculates mass attenuation per unit length.

    Args:
        energy_kev (float): energy
        photon_absorption_factor_per_unit_length (float): photon absorption factor per
        unit length
        energy_dependence_exponent (float): energy dependence exponent

    Returns:
        (float): mass attenuation per unit length.
    """
    return photon_absorption_factor_per_unit_length * (
        energy_kev**energy_dependence_exponent
    )


@validate_call()
def attenuation_at_depth_cm(
    depth_cm: NonNegativeFloat, absorption_coefficient_per_cm: NonNegativeFloat
):
    """Calculates attenuation in Barnett units, where 1000 Bn equivalent to 1/e,
    0Bn to 1 and 2000 Bn to 1/(e^2).

    Args:
        depth_cm (float): depth of absorption
        absorption_coefficient_per_cm (float): absorption coefficient per cm

    Raises:
        ValueError: If either depth_cm or absorption_coefficient are negative, an error
        is raised

    Returns:
        (float): attenuation in Barnett units
    """
    ln_t = -(depth_cm * absorption_coefficient_per_cm)
    return transmission_interconversion.attenuation_from_natural_log_of_transmission(
        ln_t
    )


@validate_call()
def thickness_cm_required_to_attenuate(
    target_attenuation_bn: NonNegativeFloat,
    absorption_coefficient_per_cm: float,
):
    """Calculates material depth in cm.

    Args:
        target_attenuation_bn (float): Target attenuation to meet in Barnett attenuation
        units.
        absorption_coefficient_per_cm (float): absorption coefficient per cm


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
    ln_target_t = (
        transmission_interconversion.natural_log_of_transmission_from_attenuation(
            target_attenuation_bn
        )
    )
    return -(ln_target_t / absorption_coefficient_per_cm)
