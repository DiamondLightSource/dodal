from pydantic import StrictFloat, validate_call


@validate_call
def photon_mass_attenuation_per_unit_length(
    energy_kev: StrictFloat,
    photon_absorption_factor_per_unit_length: StrictFloat,
    energy_dependence_exponent: StrictFloat,
) -> float:
    """Calculates mass attenuation per unit length.

    Args:
        energy_kev (StrictFloat): energy
        photon_absorption_factor_per_unit_length (StrictFloat): photon absorption factor per
        unit length
        energy_dependence_exponent (StrictFloat): energy dependence exponent

    Returns:
        (float): mass attenuation per unit length.
    """
    roll_off = energy_kev**energy_dependence_exponent
    return photon_absorption_factor_per_unit_length * roll_off
