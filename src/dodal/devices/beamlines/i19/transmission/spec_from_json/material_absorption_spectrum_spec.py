from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel

from dodal.devices.beamlines.i19.transmission.spec_from_json.energy_interval_spec import (
    EnergyIntervalSpec,
)
from dodal.devices.beamlines.i19.transmission.spec_from_json.fitted_absorption_curve_spec import (
    FittedAbsorptionCurveSpec,
)


class AbsorptionVsEnergyRelation(BaseModel):
    """JSON built dict for one element of an absorption spectrum.

    Pairs off the parameters of a fitted absorption curve,
        against the energy interval over which the curve is valid.

    Attributes:
        valid_energies: EnergyIntervalSpec
        fit_parameters: FittedAbsorptionCurveSpec
    """
    valid_energies: EnergyIntervalSpec
    fit_parameters: FittedAbsorptionCurveSpec

    # Base Model internal setting to make this class immutable
    model_config = ConfigDict(frozen=True)


class MaterialAbsorptionSpectrumSpec(BaseModel):
    """JSON built dict for the absorption spectrum of a specific material.

    Note:
        One spectrum absorption curve covers a specific energy range where it is valid.
        One or more such curves make up one absorption spectrum.

    Attributes:
        absorption_curves: List of absorption curves
    """

    absorption_curves: list[AbsorptionVsEnergyRelation] = Field(..., min_length=1)

    # Base Model internal setting to make this class immutable
    model_config = ConfigDict(frozen=True)


class MaterialAbsorptionSpectrumJson(RootModel[dict[str, list[AbsorptionVsEnergyRelation]]]):
    """Represents a JSON file where the top-level key is the material name.

    Maps material name to its absorption spectrum specification.
    """

    @classmethod
    def extract_spectrum(cls, json_blob: dict[str, Any]) -> tuple[str, MaterialAbsorptionSpectrumSpec]:
        parsed_blob = cls.model_validate(json_blob)
        material, fitted_curves = next( iter(parsed_blob.root.items() ))
        return material, MaterialAbsorptionSpectrumSpec(absorption_curves=fitted_curves)
