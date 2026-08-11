
from typing import Any, Final

import pytest

from dodal.devices.beamlines.i19.transmission.spec_from_json.material_absorption_spectrum_spec import (
    MaterialAbsorptionSpectrumJson,
    MaterialAbsorptionSpectrumSpec,
)

ALU_SPECTRUM: Final[dict[str, Any]] = {
    "aluminium": [
        {
            "valid_energies": {
                "units": "keV",
                "lower" : 5.0,
                "upper" : 30.0
            },
            "fit_parameters": {
                "photon_absorption": 64873.0,
                "roll_off":-2.96,
                "residuals_polynomial_coeffs": []
            }
        }
    ]
}

GOLD_SPECTRUM: Final[dict[str, Any]] = {
    "gold": [
      {
        "valid_energies": {
          "units": "keV",
          "lower": 5.0,
          "upper":11.5
        },
        "fit_parameters": {
          "photon_absorption": 7.87191216e5,
          "roll_off":-2.52962901,
          "residuals_polynomial_coeffs": []
        }
      },
      {
        "valid_energies": {
          "units": "keV",
          "lower": 15.0,
          "upper":30.0
        },
        "fit_parameters": {
          "photon_absorption": 3.63187927e6,
          "roll_off":-2.59815489,
          "residuals_polynomial_coeffs": []
        }
      }
    ],
}

IRON_SPECTRUM: Final[dict[str, Any]] = {
    "iron": [
      {
        "valid_energies": {
          "units": "keV",
          "lower": 8.0,
          "upper":30.0
        },
        "fit_parameters": {
          "photon_absorption": 1.034347e6,
          "roll_off":-2.8655,
          "residuals_polynomial_coeffs": []
        }
      }
    ]
}

RESIN_SPECTRUM: Final[dict[str, Any]] = {
    "resin": [
      {
        "valid_energies": {
          "units": "keV",
          "lower": 5.0,
          "upper":22.0
        },
        "fit_parameters": {
          "photon_absorption": 3814.1,
          "roll_off":-2.81706,
          "residuals_polynomial_coeffs": [
            50.9211,
            -23.6148,
            4.2138,
            -0.3814,
            1.867e-2,
            -4.709e-4,
            4.796e-6
          ]
        }
      }
    ]
}

@pytest.mark.parametrize(
    "material_spectrum_blob",
    [ALU_SPECTRUM, GOLD_SPECTRUM, IRON_SPECTRUM, RESIN_SPECTRUM]
)
def test_that_material_absorption_spectrum_can_be_built_from_dict_with_valid_content(material_spectrum_blob: dict[str, Any]):
    material_name, spectrum = MaterialAbsorptionSpectrumJson.extract_spectrum(material_spectrum_blob)

    assert material_name in ["aluminium", "gold", "iron", "resin"]
    assert isinstance(spectrum, MaterialAbsorptionSpectrumSpec)
