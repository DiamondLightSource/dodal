import math

import pytest

from dodal.common.general_maths import material_absorption_maths


# happy path
@pytest.mark.parametrize(
    "target_attenuation_bn,absorption_coefficient_per_cm,result",
    [
        (0, 2.4, 0),  # tests attenuator thickness required for transparency is zero
        (
            248.461,
            2.13,
            0.1166483568,
        ),  # tests attenuator thickness frequired for arbitrary attenuation
    ],
)
def test_thickness_cm_required_to_attenuate(
    target_attenuation_bn, absorption_coefficient_per_cm, result
):
    assert material_absorption_maths.thickness_cm_required_to_attenuate(
        target_attenuation_bn, absorption_coefficient_per_cm
    ) == pytest.approx(result, rel=1e-6)


# inauspicious path
def test_thickness_cm_required_to_attenuate_too_small_coefficient():
    with pytest.raises(ValueError):
        material_absorption_maths.thickness_cm_required_to_attenuate(1, 1e-15)


def test_thickness_required_to_attenuate_raises_negative_error():
    with pytest.raises(ValueError):
        material_absorption_maths.thickness_cm_required_to_attenuate(-1, 1)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_thickness_cm_required_to_attenuate_target_raises_error(bad_input):
    with pytest.raises(ValueError):
        material_absorption_maths.thickness_cm_required_to_attenuate(bad_input, 1.0)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_thickness_cm_required_to_attenuate_absorption_raises_error(bad_input):
    with pytest.raises(ValueError):
        material_absorption_maths.thickness_cm_required_to_attenuate(1.0, bad_input)
