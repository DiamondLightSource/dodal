import copy
import math
from typing import Any, Final

import pytest
from pydantic import ValidationError

from dodal.devices.beamlines.i19.transmission.spec_from_config.material_absorption_spectrum_spec import (
    MaterialAbsorptionSpectralConfig,
    MaterialAbsorptionSpectrumSpec,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.system_configuration import (
    SystemConfiguration,
)
from dodal.devices.beamlines.i19.transmission.spec_from_config.transmission_system_spec import (
    TransmissionSystemSpec,
)
from tests.devices.beamlines.i19.transmission.spec_from_config.fake_json import (
    FAKE_SYSTEM_SPECIFICATION_1_JSON,
    REALISTIC_SYSTEM_SPECIFICATION,
)

JSON1: Final[dict[str, dict[str, Any]]] = REALISTIC_SYSTEM_SPECIFICATION
JSON2: Final[dict[str, dict[str, Any]]] = FAKE_SYSTEM_SPECIFICATION_1_JSON

# happy path tests below


@pytest.mark.parametrize("hardware_parameters", [JSON1, JSON2])
def test_that_material_absorption_spectra_can_be_extracted_from_configuration_blob(
    hardware_parameters: dict[str, dict[str, Any]],
) -> None:
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=hardware_parameters,
    )
    all_materials: dict[str, MaterialAbsorptionSpectrumSpec] = (
        MaterialAbsorptionSpectralConfig.get_aspect_specifications(
            system_configuration=_system_config
        )
    )
    for material, spectrum in all_materials.items():
        assert spectrum is not None, f"Spectrum for {material} not found."


@pytest.mark.parametrize(
    "material_of_interest, expected_roll_off_exponents",
    [
        (
            "krypton",
            [-2.73],
        ),
        (
            "xenon",
            [-2.79],
        ),
        (
            "argon",
            [-2.6],
        ),
        (
            "neon",
            [
                -2.51,
                -2.81,
            ],
        ),
    ],
)
def test_that_material_absorption_spectra_be_collated_in_interrogatable_form(
    material_of_interest: str, expected_roll_off_exponents: list[float]
) -> None:
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=JSON2,
    )
    _extracted_spectrum = (
        MaterialAbsorptionSpectralConfig.extract_absorber_material_specifications(
            system_configuration=_system_config, material_name=material_of_interest
        )
    )
    _roll_offs = [
        curve.fit_parameters.roll_off for curve in _extracted_spectrum.absorption_curves
    ]
    assert _roll_offs == pytest.approx(expected=expected_roll_off_exponents)


# Happy path tests above

# Inauspicious path tests below


def test_that_material_absorption_spectra_rejected_if_no_materials_found_within() -> (
    None
):
    _copied_json = copy.deepcopy(JSON1)
    _copied_json["materials"] = {}  # remove all materials
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_copied_json,
    )
    with pytest.raises(ValidationError):
        MaterialAbsorptionSpectralConfig.get_aspect_specifications(
            system_configuration=_system_config
        )


def test_that_material_absorption_spectra_rejects_empty_json_blob_for_named_material() -> (
    None
):
    _copied_json = copy.deepcopy(JSON1)
    _vacuous = {"Vacuum": {}}
    _copied_json["materials"] |= _vacuous  # merge in the new "material" entry
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_copied_json,
    )
    with pytest.raises(ValidationError):
        MaterialAbsorptionSpectralConfig.get_aspect_specifications(
            system_configuration=_system_config
        )


# typo here in residuals_polynomial_coeffs <- polNYomial
TYPO_MATERIAL: Final[dict[str, Any]] = {
    "manganese": [
        {
            "valid_energies": {"units": "keV", "lower": 19.0, "upper": 30.0},
            "fit_parameters": {
                "photon_absorption": 2.037e5,
                "roll_off": -2.85,
                "residuals_polnyomial_coeffs": [],
            },
        }
    ]
}


def test_that_material_json_blob_is_rejected_with_typo() -> None:
    _copied_json = copy.deepcopy(JSON1)
    _copied_json["materials"] |= TYPO_MATERIAL  # merge in the new "material" entry
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_copied_json,
    )
    with pytest.raises(ValidationError):
        MaterialAbsorptionSpectralConfig.get_aspect_specifications(
            system_configuration=_system_config
        )


# Noting this comment on valid names for materials in the absorption spectrum part of the JSON...
# "Material name '{m}' needed to be alphanumeric or underscores, (hyphens permitted after first character)."
@pytest.mark.parametrize(
    "invalid_material_name",
    (
        "",
        " ",
        "_3",
        "-62",
        "Hg/Pb",
        "£3.75",
        "Aluminium.alloy",
        "Zr€",
        "99flake",
        " - ",
        "per: Capita",
    ),
)
def test_that_material_json_blob_is_rejected_without_valid_material_name(
    invalid_material_name: str,
) -> None:
    _misnamed_material: Final[dict[str, Any]] = {
        invalid_material_name: [
            {
                "valid_energies": {"units": "keV", "lower": 19.0, "upper": 23.0},
                "fit_parameters": {
                    "photon_absorption": 2.037e5,
                    "roll_off": -2.85,
                    "residuals_polynomial_coeffs": [],
                },
            }
        ]
    }
    _copied_json = copy.deepcopy(JSON1)
    _copied_json["materials"] |= _misnamed_material
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_copied_json,
    )
    with pytest.raises(ValidationError):
        MaterialAbsorptionSpectralConfig.get_aspect_specifications(
            system_configuration=_system_config
        )


@pytest.mark.parametrize(
    "invalid_spectrum",
    [
        "neither_a_list_nor_a_dict",
        True,
        False,
        -9.9,
        16,
        28.01,
        math.sin,
        math.pi,
        (),
        object(),
        KeyError(),
    ],
)
@pytest.mark.parametrize(
    "material_of_interest", ["aluminium", "iron", "resin1", "gold"]
)
def test_that_material_absorption_spectra_rejects_invalidly_formatted_spectrum(
    material_of_interest: str, invalid_spectrum: Any
) -> None:
    _copied_json = copy.deepcopy(JSON1)
    _copied_json["materials"][material_of_interest] = invalid_spectrum
    _system_config: SystemConfiguration = SystemConfiguration(
        structural_template=TransmissionSystemSpec,
        hardware_parameters=_copied_json,
    )
    with pytest.raises(ValidationError):
        MaterialAbsorptionSpectralConfig.get_aspect_specifications(
            system_configuration=_system_config
        )
