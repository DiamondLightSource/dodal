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
    energy_kev: Annotated[StrictFloat, Field(gt=0)],
    photon_absorption_factor_per_unit_length: Annotated[StrictFloat, Field(gt=0)],
    energy_dependence_exponent: Annotated[StrictFloat, Field(lt=0)],
) -> float:
    """Calculates mass attenuation per unit length.

    Args:
        energy_kev (StrictFloat): X-ray energy in keV (positive values only).
        photon_absorption_factor_per_unit_length (StrictFloat): Factors of e,
            in X-ray flux reduction, per unit depth of absorber (positive values only).
        energy_dependence_exponent (StrictFloat): Roll off of absorption factor (negative values only).

    Returns:
        float: Mass attenuation per unit length.
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
        depth_cm (StrictFloat): Depth of absorber (zero or positive).
        absorption_coefficient_per_cm (StrictFloat): Modelled absorption,
            (zero or positive) coefficient per cm,
            i.e. per cm factors of e reduction in flux.

    Raises:
        ValueError: If either depth_cm or absorption_coefficient are negative,
                    an error is raised, systems with optical gain are not modelled here.

    Returns:
        float: Attenuation in Barnett units of a specific depth of absorber.
    """
    ln_t = -(depth_cm * absorption_coefficient_per_cm)
    return attenuation_from_natural_log_of_transmission(ln_t)


@validate_call
def thickness_cm_required_to_attenuate(
    target_attenuation_bn: Annotated[StrictFloat, Field(ge=0)],
    absorption_coefficient_per_cm: Annotated[StrictFloat, Field(gt=1.0e-8)],
) -> float:
    """Calculates material depth in cm.

    Args:
        target_attenuation_bn (StrictFloat): Target attenuation, (zero or positive),
            in logarithmic Barnett attenuation units.
        absorption_coefficient_per_cm (StrictFloat): Factors of e per cm, reduction in flux.
            N.B. This coefficient is positive (and greater than a lower bound for realism).


    Raises:
        ValueError: if attenuation is below zero,
            or absorption is less than the lower bound set at the round magnitude 1.0e-8,
        a value error is raised
        (Bound set to a round number just below weakest absorption coefficient, of lightest gases,
         starting around 3.0e-7 per cm for H2),

    Returns:
        float: material depth in cm.
    """
    ln_target_t = natural_log_of_transmission_from_attenuation(target_attenuation_bn)
    return -(ln_target_t / absorption_coefficient_per_cm)
