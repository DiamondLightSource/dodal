import math

import pytest

from dodal.common.general_maths import transmission_interconversion


# happy:
@pytest.mark.parametrize(
    "attenuation_bn,result",
    [
        (0, 0),  # tests natural log of transparency from attenuation (canonical)
        (
            1e3,
            -1,
        ),  # tests natural log of transmission from canonical transmission is negative
        # unity (canonical)
        (
            712.6,
            -0.7126,
        ),  # tests attenuation from natural log arbitrary high transmission is -1000 *
        # attenuation
        (
            8034.1,
            -8.0341,
        ),  # tests attenuation from natural log arbitrary low transmission is -1000 *
        # attenuation
    ],
)
def test_natural_log_of_transmission_from_attenuation(attenuation_bn, result):
    assert transmission_interconversion.natural_log_of_transmission_from_attenuation(
        attenuation_bn
    ) == pytest.approx(result)


# inauspicious:
@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_natural_log_of_transmission_from_attenuation_raises_error(bad_input):
    with pytest.raises(TypeError):
        transmission_interconversion.natural_log_of_transmission_from_attenuation(
            bad_input
        )
