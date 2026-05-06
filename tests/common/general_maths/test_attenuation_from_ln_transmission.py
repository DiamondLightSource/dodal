import math

import pytest

from dodal.common.general_maths import transmission_interconversion


# happy path
@pytest.mark.parametrize(
    "ln_t,result",
    [
        (-1, 1000),  # tests negative unity log of transmission is 1000 (canonical)
        (0, 0),  # tests natural log of transparency is zero (canonical)
        (
            -0.4367,
            436.7,
        ),  # tests log from arbitrary high transmission is -1000 * log
        (
            -5.9017,
            5901.7,
        ),  # tests log from arbitrary low transmission is -1000 * log
    ],
)
def test_attenuation_from_natural_log_of_transmission(ln_t, result):
    assert transmission_interconversion.attenuation_from_natural_log_of_transmission(
        ln_t
    ) == pytest.approx(result)


# inauspicious:


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_attenuation_from_natural_log_of_transmission_raises_error(bad_input):
    with pytest.raises(TypeError):
        transmission_interconversion.attenuation_from_natural_log_of_transmission(
            bad_input
        )
