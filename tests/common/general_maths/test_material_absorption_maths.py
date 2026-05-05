import math

import pytest

from dodal.common.general_maths import material_absorption_maths


# happy path
@pytest.mark.parametrize(
    "energy_kev,photon_absorption_factor_per_unit_length,energy_dependence_exponent,"
    "result",
    [
        (5.042, 1.98e2, -2.717, 2.44170544),  # Arbitrary
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
    assert material_absorption_maths.photon_mass_attenuation_per_unit_length(
        energy_kev, photon_absorption_factor_per_unit_length, energy_dependence_exponent
    ) == pytest.approx(result)


@pytest.mark.parametrize(
    "depth_cm,absorption_coefficient_per_cm,result",
    [(0.5, 2, 1000), (1.89, 0.316, 597.24), (0.0, 2.5, 0)],
)
def test_attenuation_at_depth_cm(depth_cm, absorption_coefficient_per_cm, result):
    assert material_absorption_maths.attenuation_at_depth_cm(
        depth_cm, absorption_coefficient_per_cm
    ) == pytest.approx(result)


@pytest.mark.parametrize(
    "target_attenuation_bn,absorption_coefficient_per_cm,result",
    [
        (0, 2.4, 0),
        (248.461, 2.13, 0.1166483568),
    ],
)
def test_thickness_cm_required_to_attenuate(
    target_attenuation_bn, absorption_coefficient_per_cm, result
):
    assert material_absorption_maths.thickness_cm_required_to_attenuate(
        target_attenuation_bn, absorption_coefficient_per_cm
    ) == pytest.approx(result)


# inauspicious path
def test_attenuation_at_depth_cm_too_small_coefficient():
    with pytest.raises(ValueError):
        material_absorption_maths.thickness_cm_required_to_attenuate(1, 1e-15)


def test_attenuation_at_depth_cm_too_negative_target():
    with pytest.raises(ValueError):
        material_absorption_maths.thickness_cm_required_to_attenuate(-1, 1)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_thickness_cm_required_to_attenuate_target_error(bad_input):
    with pytest.raises(TypeError):
        material_absorption_maths.thickness_cm_required_to_attenuate(bad_input, 1.0)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_thickness_cm_required_to_attenuate_absorption_error(bad_input):
    with pytest.raises(TypeError):
        material_absorption_maths.thickness_cm_required_to_attenuate(1.0, bad_input)


@pytest.mark.parametrize("bad_input", [-1, -5, -0.1])
def test_attenuation_at_depth_cm_absorption_coefficient_error(bad_input):
    with pytest.raises(ValueError):
        material_absorption_maths.attenuation_at_depth_cm(1.0, bad_input)


@pytest.mark.parametrize("bad_input", [-1, -5, -0.1])
def test_attenuation_at_depth_cm_depth_negative_error(bad_input):
    with pytest.raises(ValueError):
        material_absorption_maths.attenuation_at_depth_cm(bad_input, 1.0)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_attenuation_at_depth_cm_depth_depth_error(bad_input):
    with pytest.raises(TypeError):
        material_absorption_maths.attenuation_at_depth_cm(bad_input, 1.0)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_attenuation_at_depth_cm_depth_absorption_error(bad_input):
    with pytest.raises(TypeError):
        material_absorption_maths.attenuation_at_depth_cm(1.0, bad_input)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_photon_mass_attenuation_per_unit_length_errors_energy(bad_input):
    with pytest.raises(TypeError):
        material_absorption_maths.photon_mass_attenuation_per_unit_length(
            bad_input, 1.0, 1.0
        )


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_photon_mass_attenuation_per_unit_length_errors_absorp(bad_input):
    with pytest.raises(TypeError):
        material_absorption_maths.photon_mass_attenuation_per_unit_length(
            1.0, bad_input, 1.0
        )


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_photon_mass_attenuation_per_unit_length_errors_expo(bad_input):
    with pytest.raises(TypeError):
        material_absorption_maths.photon_mass_attenuation_per_unit_length(
            1.0, 1.0, bad_input
        )
