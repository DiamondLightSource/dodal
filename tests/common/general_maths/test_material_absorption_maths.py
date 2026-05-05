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


# inauspicious path
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
