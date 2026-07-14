import math
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from dodal.common.general_maths.material_absorption_maths import (
    AbsorptionCalculator,
    CompoundAbsorptionCalculator,
    PolynomialAbsorptionCorrection,
    SingleRollOffAbsorptionCalculator,
    attenuation_at_depth_cm,
    photon_mass_attenuation_per_unit_length,
    thickness_cm_required_to_attenuate,
)

# happy path


# N.B. the mathematical validity of results from a simple absorption calculator
# are not tested here - since that would duplicate the validatity tests of numerical calculations
# already checked against the photon_mass_attenuation function
@patch(
    "dodal.common.general_maths.material_absorption_maths.photon_mass_attenuation_per_unit_length"
)
def test_simple_absorption_calculator_invokes_photon_mass_attenuation_calculator(
    mock_pma_calc: MagicMock,
):
    _material_factor = 3.1415926
    _roll_off = -2.71828
    calculator = SingleRollOffAbsorptionCalculator(_material_factor, _roll_off)
    _x_ray_kev = 15.6302
    calculator.absorption_coefficient_per_cm(_x_ray_kev)
    mock_pma_calc.assert_called_once_with(_x_ray_kev, _material_factor, _roll_off)


# N.B. the mathematical validity of results from a compound absorption calculator
# are not tested here - since that would duplicate the validatity tests of numerical calculations
# already checked against the contributing calculators within
def test_compound_absorption_calculator_invokes_contributing_calculators():
    mock_calcs: list[MagicMock] = [
        MagicMock(spec=AbsorptionCalculator),
        MagicMock(spec=AbsorptionCalculator),
    ]
    calcs = cast(list[AbsorptionCalculator], mock_calcs)
    compound_calculator = CompoundAbsorptionCalculator(calcs)
    _x_ray_kev = 12.6039
    compound_calculator.absorption_coefficient_per_cm(_x_ray_kev)
    for mocked_calculator in mock_calcs:
        mocked_calculator.absorption_coefficient_per_cm.assert_called_once_with(
            _x_ray_kev
        )


@pytest.mark.parametrize(
    "energy_kev, polynomial_coefficients, expected_absorption_coefficient",
    [
        (
            8.3328,
            [50.9211, -23.6148, 4.2138, -0.3814, 1.867e-2, -4.709e-4, 4.796e-6],
            -1.24317951,
        ),
        (
            12.3984,
            [43.4, -22.8148, 4.138, -0.3714, 1.967e-2, -5.709e-4, 3.796e-6],
            0.11254471963,
        ),
        (
            11.9187,
            [50.9211, -23.6148, 4.2138, -0.3814, 1.867e-2, -4.709e-4, 4.796e-6],
            -0.45286288,
        ),
    ],
)
def test_corrective_polynomial_absorption_calculator(
    energy_kev, polynomial_coefficients, expected_absorption_coefficient
):
    corrective_calculator = PolynomialAbsorptionCorrection(polynomial_coefficients)
    assert corrective_calculator.absorption_coefficient_per_cm(
        energy_kev
    ) == pytest.approx(expected_absorption_coefficient)


@pytest.mark.parametrize(
    "energy_kev, photon_absorption_factor_per_unit_length, energy_dependence_exponent, "
    "result",
    [
        (5.042, 1.98e2, -2.717, 2.44170544),  # At an arbitrary energy 5.042 keV
        (8.3328, 2.5706e3, -2.83, 6.3708311),  # Nickel energy 8.3328 keV
        (11.9187, 1.48e3, -2.93, 1.03970725),  # Gold-Three energy 11.9187 keV
        (25.514, 6.48e3, -2.41, 2.63778077),  # Silver energy 25.514 keV
        (
            20,
            1201,
            -2,
            3.0025,
        ),  # 20 keV: Test that integers, for input args, are not rejected
    ],
)
def test_photon_mass_attenuation_per_unit_length(
    energy_kev,
    photon_absorption_factor_per_unit_length,
    energy_dependence_exponent,
    result,
):
    assert photon_mass_attenuation_per_unit_length(
        energy_kev, photon_absorption_factor_per_unit_length, energy_dependence_exponent
    ) == pytest.approx(result)


@pytest.mark.parametrize(
    "target_attenuation_bn, absorption_coefficient_per_cm, required_cm",
    [
        (0, 2.4, 0),  # test that attenuator thickness required for transparency is zero
        (
            248.461,
            2.13,
            0.1166483568,
        ),  # test attenuator thickness required for arbitrary attenuation
        (
            248.461,
            2.03,
            0.12239458,
        ),  # test that greater attenuator thickness is needed when material absorbs less
        (
            448.641,
            2.13,
            0.21062958,
        ),  # test that greater attenuator thickness is needed to achieve more attenuation
    ],
)
def test_thickness_cm_required_to_attenuate(
    target_attenuation_bn, absorption_coefficient_per_cm, required_cm
):
    assert thickness_cm_required_to_attenuate(
        target_attenuation_bn, absorption_coefficient_per_cm
    ) == pytest.approx(required_cm, rel=1e-6)


@pytest.mark.parametrize(
    "depth_cm, absorption_coefficient_per_cm, result",
    [
        (
            0.5,
            2,
            1000,
        ),  # tests attenuation is 1 kilobarnett at single attenuation length
        (
            1.89,
            0.316,
            597.24,
        ),  # tests attenuation matches expectations at arbitrary attenuation depth
        (0.0, 2.5, 0),  # tests attenuation is zero after zero depth
    ],
)
def test_attenuation_at_depth_cm(depth_cm, absorption_coefficient_per_cm, result):
    assert attenuation_at_depth_cm(
        depth_cm, absorption_coefficient_per_cm
    ) == pytest.approx(result, rel=1e-6)


# inauspicious path


@pytest.mark.parametrize("negative_energy", [-0.1, -12.3, -9739.43])
def test_photon_mass_attenuation_per_unit_length_errors_with_negative_energy(
    negative_energy,
):
    _absorption_coefficient = 1.98e2
    _roll_off = -1.75
    with pytest.raises(ValidationError):
        photon_mass_attenuation_per_unit_length(
            negative_energy, _absorption_coefficient, _roll_off
        )


@pytest.mark.parametrize("invalid_energy", ["a", [], None, math.sin, object(), False])
def test_photon_mass_attenuation_per_unit_length_errors_with_invalid_energy(
    invalid_energy,
):
    _absorption_coefficient = 1.98e2
    _roll_off = -2.717
    with pytest.raises(ValidationError):
        photon_mass_attenuation_per_unit_length(
            invalid_energy, _absorption_coefficient, _roll_off
        )


@pytest.mark.parametrize(
    "invalid_absorption", ["a", [], None, math.sin, object(), False]
)
def test_photon_mass_attenuation_per_unit_length_errors_with_invalid_factor(
    invalid_absorption,
):
    _energy_kev = 4.512
    _roll_off = -2.68
    with pytest.raises(ValidationError):
        photon_mass_attenuation_per_unit_length(
            _energy_kev, invalid_absorption, _roll_off
        )


@pytest.mark.parametrize("invalid_roll_off", ["a", [], None, math.sin, object(), False])
def test_photon_mass_attenuation_per_unit_length_errors_with_invalid_exponent(
    invalid_roll_off,
):
    _energy_kev = 13.819
    _absorption_coefficient = 2.148
    with pytest.raises(ValidationError):
        photon_mass_attenuation_per_unit_length(
            _energy_kev, _absorption_coefficient, invalid_roll_off
        )


def test_thickness_cm_required_to_attenuate_rejects_transparent_medium():
    _energy_kev = 7.213
    transparent_medium = 0.0
    with pytest.raises(ValueError):
        thickness_cm_required_to_attenuate(_energy_kev, transparent_medium)


@pytest.mark.parametrize("unphysical_alpha", [1.0e-15, 3.8e-12, 7.205e-9, -1.6, -0.002])
def test_thickness_cm_required_to_attenuate_rejects_unphysical_media(unphysical_alpha):
    _target_attenuation = 750.0
    with pytest.raises(ValueError):
        thickness_cm_required_to_attenuate(_target_attenuation, unphysical_alpha)


@pytest.mark.parametrize(
    "invalid_target_attenuation", ["a", [], None, math.sin, object(), False]
)
def test_thickness_required_to_attenuate_raises_error_with_invalid_target_attenuation(
    invalid_target_attenuation,
):
    _absorption_coefficient = 2.4
    with pytest.raises(ValidationError):
        thickness_cm_required_to_attenuate(
            invalid_target_attenuation, _absorption_coefficient
        )


@pytest.mark.parametrize(
    "invalid_absorption", ["a", [], None, math.sin, object(), False]
)
def test_thickness_required_to_attenuate_raises_error_with_invalid_absorption(
    invalid_absorption,
):
    _target_attenuation = 1148.2
    with pytest.raises(ValidationError):
        thickness_cm_required_to_attenuate(_target_attenuation, invalid_absorption)


@pytest.mark.parametrize("optical_gain", [-1, -5, -0.1])
def test_attenuation_at_depth_raises_error_with_ineligible_optical_gain(optical_gain):
    _depth_cm = 0.152
    with pytest.raises(ValidationError):
        attenuation_at_depth_cm(_depth_cm, optical_gain)


@pytest.mark.parametrize("unphysical_depth", [-1, -5, -0.1])
def test_attenuation_at_depth_raises_error_for_unphysical_depths(unphysical_depth):
    _absorption_coefficient = 1.1
    with pytest.raises(ValidationError):
        attenuation_at_depth_cm(unphysical_depth, _absorption_coefficient)


@pytest.mark.parametrize("invalid_depth", ["a", [], None, math.sin, object(), True])
def test_attenuation_at_depth_raises_error_with_invalid_depth(invalid_depth):
    _absorption_coefficient = 3.7
    with pytest.raises(ValidationError):
        attenuation_at_depth_cm(invalid_depth, _absorption_coefficient)


@pytest.mark.parametrize(
    "invalid_absorption", ["a", [], None, math.tan, object(), False]
)
def test_attenuation_at_depth_raises_error_with_invalid_attenuation(invalid_absorption):
    _depth_cm = 0.425
    with pytest.raises(ValidationError):
        attenuation_at_depth_cm(_depth_cm, invalid_absorption)
