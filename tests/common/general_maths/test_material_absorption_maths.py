import math

import pytest
from pydantic import ValidationError

from dodal.common.general_maths.material_absorption_maths import (
    attenuation_at_depth_cm,
    photon_mass_attenuation_per_unit_length,
    thickness_cm_required_to_attenuate,
)


# happy path
@pytest.mark.parametrize(
    "energy_kev, photon_absorption_factor_per_unit_length, energy_dependence_exponent, "
    "result",
    [
        (5.042, 1.98e2, -2.717, 2.44170544),  # Arbitrary Energy
        (8.3328, 2.5706e3, -2.83, 6.3708311),  # Nickel
        (11.9187, 1.48e3, -2.93, 1.03970725),  # Gold-Three
        (25.514, 6.48e3, -2.41, 2.63778077),  # Silver
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
        (0, 2.4, 0),  # tests attenuator thickness required for transparency is zero
        (
            248.461,
            2.13,
            0.1166483568,
        ),  # tests attenuator thickness required for arbitrary attenuation
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
@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object(), False])
def test_photon_mass_attenuation_per_unit_length_errors_with_invalid_energy(bad_input):
    with pytest.raises(ValidationError):
        photon_mass_attenuation_per_unit_length(bad_input, 1.0, 1.0)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object(), False])
def test_photon_mass_attenuation_per_unit_length_errors_with_invalid_factor(bad_input):
    with pytest.raises(ValidationError):
        photon_mass_attenuation_per_unit_length(3500.0, bad_input, 1.0)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object(), False])
def test_photon_mass_attenuation_per_unit_length_errors_with_invalid_exponent(
    bad_input,
):
    with pytest.raises(ValidationError):
        photon_mass_attenuation_per_unit_length(3500.0, 1.0, bad_input)


def test_thickness_cm_required_to_attenuate_with_transparent_medium():
    with pytest.raises(ValueError):
        transparent_medium = 1.0e-15
        thickness_cm_required_to_attenuate(3500.0, transparent_medium)


def test_thickness_required_to_attenuate_raises_error_for_gain():
    with pytest.raises(ValidationError):
        thickness_cm_required_to_attenuate(-1, 1)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object(), False])
def test_thickness_required_to_attenuate_raises_error_with_invalid_target_attenuation(
    bad_input,
):
    with pytest.raises(ValidationError):
        thickness_cm_required_to_attenuate(bad_input, 1.0)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object(), False])
def test_thickness_required_to_attenuate_raises_error_with_invalid_absorption(
    bad_input,
):
    with pytest.raises(ValidationError):
        thickness_cm_required_to_attenuate(1.0, bad_input)


@pytest.mark.parametrize("bad_input", [-1, -5, -0.1])
def test_attenuation_at_depth_raises_error_with_invalid_absorption(bad_input):
    with pytest.raises(ValidationError):
        attenuation_at_depth_cm(1.0, bad_input)


@pytest.mark.parametrize("bad_input", [-1, -5, -0.1])
def test_attenuation_at_depth_raises_error_for_unphysical_depths(bad_input):
    with pytest.raises(ValidationError):
        attenuation_at_depth_cm(bad_input, 1.0)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object(), True])
def test_attenuation_at_depth_raises_error_with_invalid_depth(bad_input):
    with pytest.raises(ValidationError):
        attenuation_at_depth_cm(bad_input, 1.0)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object(), False])
def test_attenuation_at_depth_raises_error_with_invalid_attenuation(bad_input):
    with pytest.raises(ValidationError):
        attenuation_at_depth_cm(1.0, bad_input)
