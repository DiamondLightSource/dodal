from math import pi
from typing import Any, Final

import pytest
from pydantic import ValidationError

from dodal.devices.beamlines.i19.transmission.spec_from_config.fitted_absorption_curve_spec import (
    FittedAbsorptionCurveSpec,
)

from .utility_constants import NON_NUMERICALS

# Happy path tests

WITH_OR_WITHOUT_RESIDUALS: Final[tuple[list[float], ...]] = (
    [],
    [40.9271, -21.6924, 7.5198, -12.51, 8.87e-2, -5.39e-4, 4.796e-5],
)


@pytest.mark.parametrize("residuals", WITH_OR_WITHOUT_RESIDUALS)
@pytest.mark.parametrize(
    "roll_off",
    (
        -2.983,
        -2.83,
        -2.72,
    ),
)
@pytest.mark.parametrize(
    "scaling_constant",
    (
        3123.4,
        7812.9,
        1.305e6,
    ),
)
def test_that_fitted_absorption_curve_spec_builds_from_valid_values(
    scaling_constant: float, roll_off: float, residuals: list[float]
) -> None:
    d: dict[str, Any] = {
        "photon_absorption": scaling_constant,
        "roll_off": roll_off,
        "residuals_polynomial_coeffs": residuals,
    }
    assert FittedAbsorptionCurveSpec(**d) is not None


@pytest.mark.parametrize(
    "roll_off",
    (
        -2.983,
        -2.83,
        -2.72,
    ),
)
@pytest.mark.parametrize(
    "scaling_constant",
    (
        3123.4,
        7812.9,
        1.305e6,
    ),
)
def test_that_fitted_absorption_curve_spec_builds_when_residuals_are_in_tuple(
    scaling_constant: float, roll_off: float
) -> None:
    _residuals_tuple: tuple[float, ...] = (-1.5, 0.03, 16.8, -272.345)
    d: dict[str, Any] = {
        "photon_absorption": scaling_constant,
        "roll_off": roll_off,
        "residuals_polynomial_coeffs": _residuals_tuple,
    }
    assert FittedAbsorptionCurveSpec(**d) is not None


# Inauspicious path tests


@pytest.mark.parametrize("residuals", WITH_OR_WITHOUT_RESIDUALS)
@pytest.mark.parametrize("non_positive_scaling_constant", (0, -2.8, -2903.4))
def test_that_non_positive_scaling_constants_rejected_by_fitted_absorption_curve_spec(
    non_positive_scaling_constant: float, residuals: list[float]
) -> None:
    d: dict[str, Any] = {
        "photon_absorption": non_positive_scaling_constant,
        "roll_off": -2.78,
        "residuals_polynomial_coeffs": residuals,
    }
    with pytest.raises(ValidationError):
        FittedAbsorptionCurveSpec(**d)


@pytest.mark.parametrize(
    "residuals",
    WITH_OR_WITHOUT_RESIDUALS,
)
@pytest.mark.parametrize(
    "non_numerical_scaling_constant",
    NON_NUMERICALS,
)
def test_that_non_numerical_scaling_constants_rejected_by_fitted_absorption_curve_spec(
    non_numerical_scaling_constant: Any, residuals: list[float]
) -> None:
    d: dict[str, Any] = {
        "photon_absorption": non_numerical_scaling_constant,
        "roll_off": -2.78,
        "residuals_polynomial_coeffs": residuals,
    }
    with pytest.raises(ValidationError):
        FittedAbsorptionCurveSpec(**d)


UNPHYSICAL_ROLL_OFF_EXPONENTS: Final[list[float]] = [
    1.2,
    2.96,
    -1.5,
    -4.5,
    -296,
    -1,
    pi,
    1,
    4,
    44.8,
    200004,
    -1289,
]


@pytest.mark.parametrize(
    "residuals",
    WITH_OR_WITHOUT_RESIDUALS,
)
@pytest.mark.parametrize(
    "unphysical_exponent",
    UNPHYSICAL_ROLL_OFF_EXPONENTS,
)
def test_that_unphysical_roll_off_exponent_rejected_by_fitted_absorption_curve_spec(
    unphysical_exponent: float, residuals: list[float]
) -> None:
    d: dict[str, Any] = {
        "photon_absorption": 53408.9,
        "roll_off": unphysical_exponent,
        "residuals_polynomial_coeffs": residuals,
    }
    with pytest.raises(ValidationError):
        FittedAbsorptionCurveSpec(**d)


@pytest.mark.parametrize(
    "residuals",
    WITH_OR_WITHOUT_RESIDUALS,
)
@pytest.mark.parametrize(
    "non_numerical_exponent",
    NON_NUMERICALS,
)
def test_that_non_numerical_roll_off_exponent_rejected_by_fitted_absorption_curve_spec(
    non_numerical_exponent: Any, residuals: list[float]
) -> None:
    d: dict[str, Any] = {
        "photon_absorption": 53408.9,
        "roll_off": non_numerical_exponent,
        "residuals_polynomial_coeffs": residuals,
    }
    with pytest.raises(ValidationError):
        FittedAbsorptionCurveSpec(**d)


@pytest.mark.parametrize(
    "non_numerical",
    NON_NUMERICALS,
)
def test_that_non_numerical_residual_rejected_by_fitted_absorption_curve_spec(
    non_numerical: Any,
) -> None:
    _corrupted_residuals = [1.9, -9.1, non_numerical, -428.01312]
    d: dict[str, Any] = {
        "photon_absorption": 63091.2,
        "roll_off": -2.78,
        "residuals_polynomial_coeffs": _corrupted_residuals,
    }
    with pytest.raises(ValidationError):
        FittedAbsorptionCurveSpec(**d)


@pytest.mark.parametrize(
    "stringy_residuals",
    "[1.9, 27.8, -55.81, -206.11]",
)
def test_that_string_residuals_rejected_by_fitted_absorption_curve_spec(
    stringy_residuals: str,
) -> None:
    d: dict[str, Any] = {
        "photon_absorption": 63091.2,
        "roll_off": -2.78,
        "residuals_polynomial_coeffs": stringy_residuals,
    }
    with pytest.raises(ValidationError):
        FittedAbsorptionCurveSpec(**d)
