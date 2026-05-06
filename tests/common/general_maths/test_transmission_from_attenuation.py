import math

import pytest

from dodal.common.general_maths import transmission_interconversion


# happy:
@pytest.mark.parametrize(
    "attenuation_bn,result",
    [
        (0, 1),  # tests transparency from zero attenuation (canonical)
        (
            1e3,
            0.3678794,
        ),  # tests transmission from canonical attenuation is  1/e (canonical)
        (
            145.1,
            0.8649358,
        ),  # tests transmission from arbitrary weak attenuation is -1000*attenuation
        (
            7221.9,
            7.3041331435179e-4,
        ),  # tests transmission from arbitrary strong attenuation is -1000*attenuation
    ],
)
def test_transmission_from_attenutation(attenuation_bn, result):
    assert transmission_interconversion.transmission_from_attenutation(
        attenuation_bn
    ) == pytest.approx(result)


# inauspicious:


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_transmission_from_attenutation_raises_error(bad_input):
    with pytest.raises(TypeError):
        transmission_interconversion.transmission_from_attenutation(bad_input)
