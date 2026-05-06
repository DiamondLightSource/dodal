import math

import pytest

from dodal.common.general_maths import transmission_interconversion

# happy:


@pytest.mark.parametrize(
    "transmission_as_fraction,result",
    [
        (1, 0),  # tests attenuation from transparency is zero (canonical)
        (0.37, 994.25227334),  # tests attenuation from 37% is close to 1000 (canonical)
        (
            0.871,
            138.1133,
        ),  # tests attenuation from arbitrary high transmission has expected value
        (
            4.2e-4,
            7775.2558,
        ),  # tests attenuation from arbitrary high attenuation has expected value
    ],
)
def test_attenuation_from_transmission(transmission_as_fraction, result):
    assert transmission_interconversion.attenuation_from_transmission(
        transmission_as_fraction
    ) == pytest.approx(result)


# inauspicious:


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_attenuation_from_transmission_raises_error(bad_input):
    with pytest.raises(TypeError):
        transmission_interconversion.attenuation_from_transmission(bad_input)
