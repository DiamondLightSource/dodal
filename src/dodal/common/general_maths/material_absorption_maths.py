from collections.abc import Callable
from typing import Annotated, Final, Protocol, runtime_checkable

from numpy.polynomial import polynomial
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictFloat,
    validate_call,
)

from dodal.common.general_maths.interval import ClosedInterval
from dodal.common.general_maths.transmission_interconversion import (
    attenuation_from_natural_log_of_transmission,
    natural_log_of_transmission_from_attenuation,
)


@runtime_checkable
class AbsorptionCalculator(Protocol):
    """Interface for calculating absorption (due to mass attenuation) per cm as a function of x-ray energy in keV.

    Reports back a natural log based absorption factor as function of x-ray energy.
    """

    def absorption_coefficient_per_cm(
        self, *, energy_kev: Annotated[StrictFloat, Field(gt=0)]
    ) -> float:
        """Logarithmic contribution to x-ray absorption per cm (depth into absorber) at a particular photon energy.

        Notes:
        1) The cm as a typical unit length scale is a de facto standard in the field.
        2a) The absorption coefficient is in factors of e.
        2b) Barnett absorption units are only used once this coefficient is combined with depth in cm.
        3a) Negative contributions to a sum have to be permitted so the output,
            of a specific calculator instance, can be a float of either sign.
        3b) Sub-classes may implicitly restrict this expectation.
            Real materials the final absorption will be positive.

        Args:
            energy_kev (StrictFloat): The individual energy per photon in kilo-electronvolts

        Returns:
            (float): Model adjustment of attenuation per cm of absorber material depth.
        """
        ...


class BaseAbsorptionCalculator(AbsorptionCalculator):
    def __init__(self, _calculation: Callable[[float], float]):
        # store the calculator functionality in the base class
        self._calculate: Final[Callable[[float], float]] = _calculation

    @validate_call
    def absorption_coefficient_per_cm(
        self, *, energy_kev: Annotated[StrictFloat, Field(gt=0)]
    ) -> float:
        return self._calculate(energy_kev)


class CompoundAbsorptionCalculator(BaseAbsorptionCalculator):
    """Advanced physics model for mass attenuation per cm as a function of x-ray energy in keV.

    Applies effects from several absorption term calculations.

    Attributes:
        contributers (list[AbsorptionCalculator])
    """

    def __init__(self, *, contributions: list[AbsorptionCalculator]):
        super().__init__(
            # lambda k is energy in keV
            lambda k: sum(
                c.absorption_coefficient_per_cm(energy_kev=k) for c in contributions
            )
        )


class PolynomialAbsorptionCorrection(BaseAbsorptionCalculator):
    """Corrective model for mass attenuation per cm as a function of x-ray energy in keV.
    Provides terms for correcting a baseline mass attenuation.

    Attributes:
        corrective_terms (float): Polynomial coefficients to correct the baseline modelled absorption per cm
    """

    def __init__(self, *, coefficients_per_cm: list[float]):

        def _calculate_correction(energy_kev: float) -> float:
            correction = polynomial.polyval(energy_kev, coefficients_per_cm)
            return float(correction)  # numpy did not specify float as the return type

        super().__init__(_calculate_correction)


class SingleRollOffAbsorptionCalculator(BaseAbsorptionCalculator):
    """Simplest physics model for mass attenuation per cm as a function of x-ray energy in keV.

    Typically appropriate where one element dominates the absorption,
    and energies passed in as calculation arguments are above the elements absorption resonance edge.

    Attributes:
        material_factor_per_cm (StrictFloat): Positive non-zero material constant
        (hypothetical trend offset equivalent to an absorption per cm at 1 keV)
        roll_off: negative exponent of energy dependence above the resonant edge.
    """

    def __init__(
        self,
        *,
        material_factor_per_cm: Annotated[StrictFloat, Field(gt=0)],
        roll_off: Annotated[StrictFloat, Field(lt=0)],
    ):
        # lambda k is energy in keV
        super().__init__(
            lambda k: photon_mass_attenuation_per_unit_length(
                energy_kev=k,
                photon_absorption_factor_per_unit_length=material_factor_per_cm,
                energy_dependence_exponent=roll_off,
            )
        )


class AbsorptionSpectrumSegment(BaseModel):
    """Pairing off of an energy interval against a particular parameterised absorption calculator.

    Attributes:
        kev_energy_interval: An inclusive, continuous energy interval.
        absorption_calculator: An energy appropriate absorption calculator.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    kev_energy_interval: ClosedInterval
    absorption_calculator: AbsorptionCalculator


class MaterialAbsorptionSpectrum(BaseModel):
    """Mapping across N x-ray energy intervals, of interval specific absorption calculator(s).

    For a given material, one or more energy ranges (in keV) will each have a model calculating the "regional" absorption curve.

    Attributes:
        intervals: A tuple of AbsorptionIntervalModels


    Example:
        ```python
        spectrum = MaterialAbsorptionSpectrum(
            intervals=(
                AbsorptionIntervalModel(
                    kev_energy_range=ClosedInterval(lower=5.0, upper=12.3),
                    absorption_calculator=SingleRollOffAbsorptionCalculator(
                        material_factor_per_cm=3145.8, roll_off=-2.94
                    )
                ),
                AbsorptionIntervalModel(
                    kev_energy_range=ClosedInterval(lower=22.0, upper=50.0),
                    absorption_calculator=SingleRollOffAbsorptionCalculator(
                        material_factor_per_cm=1145.1, roll_off=-3.27
                    )
                )
            )
        )
        ```
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)
    intervals: tuple[AbsorptionSpectrumSegment, ...] = Field(
        default_factory=tuple,
        description="Sequence of energy intervals with their specific absorption curve calculator",
        min_length=1,
    )

    def absorption_coefficient_per_cm(
        self, *, energy_kev: Annotated[StrictFloat, Field(gt=0)]
    ) -> float:
        """Logarithmic contribution to x-ray absorption per cm (depth into absorber) at a particular photon energy.

        Notes:
        1) The cm as a typical unit length scale is a de facto standard in the field.
        2a) The absorption coefficient is in factors of e.
        2b) Barnett absorption units are only used once this coefficient is combined with depth in cm.
        3a) Negative contributions to a sum have to be permitted so the output,
            of a specific calculator instance, can be a float of either sign.
        3b) Sub-classes may implicitly restrict this expectation.
            Real materials the final absorption will be positive.

        Args:
            energy_kev (StrictFloat): The individual energy per photon in kilo-electronvolts

        Returns:
            (float): Model adjustment of attenuation per cm of absorber material depth.
        """
        # Iterate sequentially through our modelled energy intervals
        for absorption_model in self.intervals:
            if energy_kev in absorption_model.kev_energy_interval:
                absorption_coeff = (
                    absorption_model.absorption_calculator.absorption_coefficient_per_cm
                )
                return absorption_coeff(energy_kev=energy_kev)
        _msg = f"Absorption of x-ray energy at {energy_kev} keV is outside the valid interval of any calculator in this modelled spectrum."
        raise ValueError(_msg)


@validate_call
def photon_mass_attenuation_per_unit_length(
    energy_kev: Annotated[StrictFloat, Field(gt=0)],
    photon_absorption_factor_per_unit_length: Annotated[StrictFloat, Field(gt=0)],
    energy_dependence_exponent: Annotated[StrictFloat, Field(lt=0)],
) -> float:
    """Calculates mass attenuation per unit length.

    See for example: https://en.wikipedia.org/wiki/Mass_attenuation_coefficient.

    Args:
        energy_kev (StrictFloat): X-ray energy in keV (positive values only).
        photon_absorption_factor_per_unit_length (StrictFloat): Logarithmic constant, scaled in factors of e.
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
    absorption_coefficient_per_cm: Annotated[StrictFloat, Field(gt=0)],
) -> float:
    """Calculates attenuation in Barnett units, where 1000 Bn equivalent to 1/e,
    0 Bn to 1 and 2000 Bn to 1/(e^2).

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
