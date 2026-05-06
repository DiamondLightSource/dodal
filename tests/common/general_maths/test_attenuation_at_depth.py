import math

import pytest

from dodal.common.general_maths import material_absorption_maths


# happy path
@pytest.mark.parametrize(
    "depth_cm,absorption_coefficient_per_cm,result",
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
    assert material_absorption_maths.attenuation_at_depth_cm(
        depth_cm, absorption_coefficient_per_cm
    ) == pytest.approx(result, rel=1e-6)


# inauspicious path


@pytest.mark.parametrize("bad_input", [-1, -5, -0.1])
def test_attenuation_at_depth_cm_absorption_coefficient_error(bad_input):
    with pytest.raises(ValueError):
        material_absorption_maths.attenuation_at_depth_cm(1.0, bad_input)


@pytest.mark.parametrize("bad_input", [-1, -5, -0.1])
def test_attenuation_at_depth_cm_depth_raises_negative_error(bad_input):
    with pytest.raises(ValueError):
        material_absorption_maths.attenuation_at_depth_cm(bad_input, 1.0)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_attenuation_at_depth_cm_depth_depth_raises_error(bad_input):
    with pytest.raises(ValueError):
        material_absorption_maths.attenuation_at_depth_cm(bad_input, 1.0)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_attenuation_at_depth_cm_depth_absorption_raises_error(bad_input):
    with pytest.raises(ValueError):
        material_absorption_maths.attenuation_at_depth_cm(1.0, bad_input)
