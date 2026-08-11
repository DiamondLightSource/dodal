import math
from typing import Any

import pytest
from pydantic import ValidationError

from dodal.devices.beamlines.i19.transmission.json_expected_structures import (
    AbsorptionCurveFitParametersJsonValidation,
    EnergyIntervalJsonValidation,
)

# Happy path tests


@pytest.mark.parametrize(
    "upper_bound",
    (
        2.2,
        3,
        17.8,
        24.001,
        25.7,
        27,
        28.9,
    ),
)
@pytest.mark.parametrize(
    "lower_bound",
    (
        0.2,
        0.5,
        1,
        1.6,
        2,
    ),
)
@pytest.mark.parametrize(
    "energy_unit",
    (
        "keV",
        "kiloelectronvolts",
    ),
)
def test_that_energy_interval_json_validation_can_be_built_from_dict_with_valid_energy_units(
    energy_unit: str, lower_bound: float, upper_bound: float
) -> None:
    d: dict[str, Any] = {
        "units": energy_unit,
        "lower": lower_bound,
        "upper": upper_bound,
    }
    assert EnergyIntervalJsonValidation(**d) is not None


@pytest.mark.parametrize(
    "residuals",
    ([], [50.9211, -23.6148, 4.2138, -0.3814, 1.867e-2, -4.709e-4, 4.796e-6]),
)
@pytest.mark.parametrize("roll_off", (-3.1, -3, -2.983, -2.83, -2.72, -2.56, -2.414))
@pytest.mark.parametrize(
    "scaling_constant",
    (
        3123.4,
        7812.9,
        12045.72,
        733802.8512,
        1.305e6,
    ),
)
def test_that_absorption_curve_fit_json_validation_can_be_built_from_dict_with_valid_values(
    scaling_constant: float, roll_off: float, residuals: list[float]
) -> None:
    d: dict[str, Any] = {
        "photon_absorption": scaling_constant,
        "roll_off": roll_off,
        "residuals_polynomial_coeffs": residuals,
    }
    assert AbsorptionCurveFitParametersJsonValidation(**d) is not None


# Inauspicious path tests


@pytest.mark.parametrize(
    "upper_bound",
    (
        2.2,
        27,
        28.9,
    ),
)
@pytest.mark.parametrize(
    "lower_bound",
    (
        0.2,
        0.5,
        1,
    ),
)
@pytest.mark.parametrize(
    "key",
    (
        "unitz",
        "Units",
        "Unit",
        "unit",
        "u",
        "lower",
        "upper",
    ),
)
def test_that_energy_interval_json_validation_fails_with_typo_in_units_bound_key(
    key: str, lower_bound: float, upper_bound: float
) -> None:
    d: dict[str, Any] = {key: "keV", "lower": lower_bound, "upper": upper_bound}
    with pytest.raises(ValidationError):
        EnergyIntervalJsonValidation(**d)


@pytest.mark.parametrize(
    "upper_bound",
    (
        2.2,
        27,
        28.9,
    ),
)
@pytest.mark.parametrize(
    "lower_bound",
    (
        0.2,
        0.5,
        1,
    ),
)
@pytest.mark.parametrize("key", ("loewr", "Lower", "LR", "l0wer", "upper", "units"))
def test_that_energy_interval_json_validation_fails_with_typo_in_lower_bound_key(
    key: str, lower_bound: float, upper_bound: float
) -> None:
    d: dict[str, Any] = {"units": "keV", key: lower_bound, "upper": upper_bound}
    with pytest.raises(ValidationError):
        EnergyIntervalJsonValidation(**d)


@pytest.mark.parametrize(
    "upper_bound",
    (
        2.2,
        27,
        28.9,
    ),
)
@pytest.mark.parametrize(
    "lower_bound",
    (
        0.2,
        0.5,
        1,
    ),
)
@pytest.mark.parametrize(
    "key", ("uppre", "Upper", "UR", "uPper", "UPPER", "lower", "units")
)
def test_that_energy_interval_json_validation_fails_with_typo_in_upper_bound_key(
    key: str, lower_bound: float, upper_bound: float
) -> None:
    d: dict[str, Any] = {"units": "keV", "lower": lower_bound, key: upper_bound}
    with pytest.raises(ValidationError):
        EnergyIntervalJsonValidation(**d)


@pytest.mark.parametrize(
    "unsupported_units",
    (
        "meV",
        "KILOelectronvolts",
        "kev",
        "k_eV",
        "MeV",
        "mV",
        "J",
        "Joules",
        "s",
        "GBq",
    ),
)
def test_that_energy_interval_json_validation_rejects_unsupported_energy_units(
    unsupported_units,
) -> None:
    d: dict[str, Any] = {"units": unsupported_units, "lower": 2.1, "upper": 11.5}
    with pytest.raises(ValidationError):
        EnergyIntervalJsonValidation(**d)


@pytest.mark.parametrize(
    "invalid_energy_units",
    ("", "*^&", 16, math.cos, KeyError(), object(), "-9", -9.0, math.pi, True, False),
)
def test_that_energy_interval_json_validation_rejects_invalid_energy_units(
    invalid_energy_units,
) -> None:
    d: dict[str, Any] = {"units": invalid_energy_units, "lower": 2.1, "upper": 11.5}
    with pytest.raises(ValidationError):
        EnergyIntervalJsonValidation(**d)


@pytest.mark.parametrize(
    "upper_bound",
    (
        3.9,
        3.75,
        3.4,
        3,
        2.9,
        2.405,
        math.e,
        2.17,
        1.7,
        0.89,
    ),
)
@pytest.mark.parametrize(
    "high_lower_bound",
    (
        4,
        5.0,
        12,
        6.7,
        44.1,
        8009.23,
        23,
    ),
)
def test_that_energy_interval_json_validation_rejects_bounds_when_lower_bound_above_upper_bound(
    high_lower_bound: float, upper_bound: float
) -> None:
    d: dict[str, Any] = {
        "units": "keV",
        "lower": high_lower_bound,
        "upper": upper_bound,
    }
    with pytest.raises(ValidationError):
        EnergyIntervalJsonValidation(**d)


@pytest.mark.parametrize(
    "invalid_lower_bound",
    (
        -math.pi,
        -12,
        -100.89,
        -0.03,
        -1.4,
        -2,
    ),
)
def test_that_energy_interval_json_validation_rejects_negative_lower_bound(
    invalid_lower_bound,
) -> None:
    d: dict[str, Any] = {"units": "keV", "lower": invalid_lower_bound, "upper": 25}
    with pytest.raises(ValidationError):
        EnergyIntervalJsonValidation(**d)


NON_NUMERICALS = (
    math.sin,
    object(),
    ValueError(),
    "312",
    "*$",
    "",
    " ",
    "Hello World",
    "7.6",
    True,
    False,
)


@pytest.mark.parametrize("non_numerical_lower_bound", NON_NUMERICALS)
def test_that_energy_interval_json_validation_rejects_non_numerical_lower_bound(
    non_numerical_lower_bound,
) -> None:
    d: dict[str, Any] = {
        "units": "keV",
        "lower": non_numerical_lower_bound,
        "upper": 28.54,
    }
    with pytest.raises(ValidationError):
        EnergyIntervalJsonValidation(**d)


@pytest.mark.parametrize("non_numerical_upper_bound", NON_NUMERICALS)
def test_that_energy_interval_json_validation_rejects_non_numerical_upper_bound(
    non_numerical_upper_bound,
) -> None:
    d: dict[str, Any] = {
        "units": "keV",
        "lower": 15.25,
        "upper": non_numerical_upper_bound,
    }
    with pytest.raises(ValidationError):
        EnergyIntervalJsonValidation(**d)
