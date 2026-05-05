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


def attenuation_at_depth_cm(depth_cm: float, absorption_coefficient_per_cm: float):
    # TODO: check this - not sure if it really is the depth of the wedge?
    """Calculates attenuation in Barnett units.

    Args:
        depth_cm (float): depth of wedge
        absorption_coefficient_per_cm (float): absorption coefficient per cm

    Raises:
        ValueError: If either input value for either depth_cm or absorption_coefficient_
        per_cm <0.0, raises a value error.

    Returns:
        (float): attenuation in Barnett units
    """
    if depth_cm < 0.0:
        raise ValueError(f"Negative depth is an invalid input: {depth_cm}")
    if absorption_coefficient_per_cm < 0.0:
        raise ValueError(
            "Invalid absorption, this calculator is no for systems with\
                         optical gain."
        )
    return transmission_interconversion.attenuation_from_natural_log_of_transmission(
        -(depth_cm * absorption_coefficient_per_cm)
    )


def thickness_cm_required_to_attenuate(
    target_attenuation_bn: float,
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
    if (
        target_attenuation_bn < 0.0
        or absorption_coefficient_per_cm < minimum_meaningful_absorption_coefficient
    ):
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
