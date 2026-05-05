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
    roll_off = energy_kev**energy_dependence_exponent
    return photon_absorption_factor_per_unit_length * roll_off
