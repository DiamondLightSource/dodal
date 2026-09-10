from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from dodal.common.general_maths.interval import ClosedInterval
from dodal.common.general_maths.material_absorption_maths import (
    AbsorptionCalculator,
    AbsorptionSpectrumSegment,
    CompoundAbsorptionCalculator,
    MaterialAbsorptionSpectrum,
    PolynomialAbsorptionCorrection,
    SingleRollOffAbsorptionCalculator,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.energy_interval_spec import (
    EnergyIntervalSpec,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.fitted_absorption_curve_spec import (
    FittedAbsorptionCurveSpec,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.name_validation import (
    MaterialNameValidation,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.system_aspect_base_parser import (
    SystemAspectBaseParser,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.system_configuration import (
    SystemConfiguration,
)


class AbsorptionVsEnergyRelation(BaseModel):
    """Configuration dict for one piece of an absorption spectrum, one energy range specific fit curve.

    Note:
        This relation class is a pairing.  The internal pair consists of :
        - The x-ray energy interval over which this piece of the spectrum is valid (a.k.a. domain).
        - The parameters of a fitted absorption curve.

    Attributes:
        valid_energies: Specifies x-ray energy *domain* valid for the fitted curve.
        fit_parameters: Specifies parameters needed to calculate absorption values on the fitted curve.

    *See also, these closely related classes:*
        **FittedAbsorptionCurveSpec**: Fitted curve specification
        **EnergyIntervalSpec**: Energy range (interval) specification
        **ClosedInterval**: General maths class underpinning interval definition
    """

    valid_energies: EnergyIntervalSpec
    fit_parameters: FittedAbsorptionCurveSpec

    # Base Model internal setting to make this class immutable
    model_config = ConfigDict(frozen=True, extra="forbid")

    def as_spectrum_segment(self) -> AbsorptionSpectrumSegment:
        base_calculator = SingleRollOffAbsorptionCalculator(
            material_factor_per_cm=self.fit_parameters.photon_absorption,
            roll_off=self.fit_parameters.roll_off,
        )
        corrections: list[float] = [
            float(c) for c in self.fit_parameters.residuals_polynomial_coeffs
        ]
        no_corrections: bool = len(corrections) < 1
        calculator: AbsorptionCalculator = (
            base_calculator
            if no_corrections
            else CompoundAbsorptionCalculator(
                contributions=[
                    base_calculator,
                    PolynomialAbsorptionCorrection(coefficients_per_cm=corrections),
                ]
            )
        )
        energy_interval: ClosedInterval = self.valid_energies.as_interval
        return AbsorptionSpectrumSegment(
            kev_energy_interval=energy_interval, absorption_calculator=calculator
        )


class MaterialAbsorptionSpectrumSpec(BaseModel):
    """Configuration dict for the absorption spectrum of a specific material.

    Note:
        One spectrum absorption curve covers a specific energy range where it is valid.
        One or more such curves make up one absorption spectrum.

    Attributes:
        absorption_curves: List of absorption curves
    """

    absorption_curves: list[AbsorptionVsEnergyRelation] = Field(..., min_length=1)

    # Base Model internal setting to make this class immutable and valid
    model_config = ConfigDict(frozen=True, extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def _coerce_raw_list_to_absorption_curves_dict(cls, data: Any) -> Any:
        """Wrap spectrum pieces listing internally as a dict."""
        if isinstance(data, list):
            return {"absorption_curves": data}
        if isinstance(data, dict):
            return data
        raise ValueError(
            "Absorption spectrum data should be a list or dict of fitted curves."
        )

    def as_spectrum(self) -> MaterialAbsorptionSpectrum:
        segments: list[AbsorptionSpectrumSegment] = [
            k.as_spectrum_segment() for k in self.absorption_curves
        ]
        return MaterialAbsorptionSpectrum(intervals=tuple(segments))


class MaterialAbsorptionSpectralConfig(
    SystemAspectBaseParser[MaterialAbsorptionSpectrumSpec]
):
    """Configuration dict for the absorption spectra of all specified absorber materials.

    Maps each material name to its absorption spectrum specification, as extracted from configuration (JSON).

    Note:
        Base class does most of the work - except for material name validation.
    """

    def validate_key_name(self, *, key_name: str) -> None:
        MaterialNameValidation.validate_material_name(material_name=key_name)

    @field_validator("root")
    @classmethod
    def _ensure_at_least_one_absorber_material_has_been_specified(
        cls,
        all_absorber_materials_specifications: dict[
            str, MaterialAbsorptionSpectrumSpec
        ],
    ) -> dict[str, MaterialAbsorptionSpectrumSpec]:
        """Invalidates configuration if that features zero absorber materials.

        Raises:
            ValueError - if no absorbers are present.
        """
        _specified_absorber_materials = all_absorber_materials_specifications.keys()
        if len(_specified_absorber_materials) < 1:
            raise ValueError(
                "Empty absorber materials configuration! This is not valid input."
            )
        return all_absorber_materials_specifications

    @classmethod
    def extract_absorber_material_specifications(
        cls,
        *,
        system_configuration: SystemConfiguration,
        material_name: str,
    ) -> MaterialAbsorptionSpectrumSpec:
        """Extracts the absorption spectrum specification for a specific material."""
        _materials_spectra: dict[str, MaterialAbsorptionSpectrumSpec] = (
            cls.get_aspect_specifications(system_configuration=system_configuration)
        )
        return _materials_spectra[material_name]
