import math
from typing import Any

import pytest
from pydantic import ValidationError

from dodal.devices.beamlines.i19.transmission.spec_from_json.energy_interval_spec import (
    EnergyIntervalSpec,
)

from .utility_constants import (
    INVALID_ENERGY_UNITS,
    NON_NUMERICALS,
    UNSUPPORTED_ENERGY_UNITS,
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
def test_that_energy_interval_spec_can_be_built_from_dict_with_valid_energy_units(
    energy_unit: str, lower_bound: float, upper_bound: float
) -> None:
    d: dict[str, Any] = {
        "units": energy_unit,
        "lower": lower_bound,
        "upper": upper_bound,
    }
    assert EnergyIntervalSpec(**d) is not None


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
        EnergyIntervalSpec(**d)


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
        EnergyIntervalSpec(**d)


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
        EnergyIntervalSpec(**d)


@pytest.mark.parametrize(
    "unsupported_units",
    UNSUPPORTED_ENERGY_UNITS
)
def test_that_energy_interval_json_validation_rejects_unsupported_energy_units(
    unsupported_units,
) -> None:
    d: dict[str, Any] = {"units": unsupported_units, "lower": 2.1, "upper": 11.5}
    with pytest.raises(ValidationError):
        EnergyIntervalSpec(**d)


@pytest.mark.parametrize(
    "invalid_energy_units",
    INVALID_ENERGY_UNITS,
)
def test_that_energy_interval_json_validation_rejects_invalid_energy_units(
    invalid_energy_units,
) -> None:
    d: dict[str, Any] = {"units": invalid_energy_units, "lower": 2.1, "upper": 11.5}
    with pytest.raises(ValidationError):
        EnergyIntervalSpec(**d)


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
        EnergyIntervalSpec(**d)


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
        EnergyIntervalSpec(**d)


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
        EnergyIntervalSpec(**d)


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
        EnergyIntervalSpec(**d)
