import math

import pytest
from pydantic import ValidationError

from dodal.common.general_maths.transmission_interconversion import (
    attenuation_from_natural_log_of_transmission,
    attenuation_from_transmission,
    natural_log_of_transmission_from_attenuation,
    transmission_from_attenutation,
)


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
        ),  # tests transmission from arbitrary weak attenuation is weak attenuation
        (
            7221.9,
            7.3041331435179e-4,
        ),  # tests transmission from arbitrary strong attenuation is strong attenuation
    ],
)
def test_transmission_from_attenutation(attenuation_bn, result):
    assert transmission_from_attenutation(attenuation_bn) == pytest.approx(result)


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
        ),  # tests attenuation from natural log arbitrary high transmission
        (
            8034.1,
            -8.0341,
        ),  # tests attenuation from natural log arbitrary low transmission
    ],
)
def test_natural_log_of_transmission_from_attenuation(attenuation_bn, result):
    assert natural_log_of_transmission_from_attenuation(
        attenuation_bn
    ) == pytest.approx(result)


@pytest.mark.parametrize(
    "transmission_as_fraction,result",
    [
        (1, 0),  # tests attenuation from transparency is zero (canonical)
        (0.37, 994.25227334),  # tests attenuation from 37% is close to 1000
        (
            0.871,
            138.1133,
        ),  # tests attenuation from arbitrary high transmission
        (
            4.2e-4,
            7775.2558,
        ),  # tests attenuation from arbitrary high attenuation
    ],
)
def test_attenuation_from_transmission(transmission_as_fraction, result):
    assert attenuation_from_transmission(transmission_as_fraction) == pytest.approx(
        result
    )


@pytest.mark.parametrize(
    "ln_t,result",
    [
        (-1, 1000),  # tests negative unity log of transmission is 1000 (canonical)
        (0, 0),  # tests natural log of transparency is zero (canonical)
        (
            -0.4367,
            436.7,
        ),  # tests log from arbitrary high transmission
        (
            -5.9017,
            5901.7,
        ),  # tests log from arbitrary low transmission
    ],
)
def test_attenuation_from_natural_log_of_transmission(ln_t, result):
    assert attenuation_from_natural_log_of_transmission(ln_t) == pytest.approx(result)


# Circular tests (all numbers here arbitrary)


@pytest.mark.parametrize("input", [1.0, 10.0, 100.0])
def test_circular_attenuation_from_log_and_back(input):
    assert (
        attenuation_from_natural_log_of_transmission(
            natural_log_of_transmission_from_attenuation(input)
        )
        == input
    )
    assert (
        natural_log_of_transmission_from_attenuation(
            attenuation_from_natural_log_of_transmission(input)
        )
        == input
    )


@pytest.mark.parametrize("input", [1.0, 10.0, 100.0])
def test_circular_attenuation_from_transmission_and_back(input):
    assert attenuation_from_transmission(
        transmission_from_attenutation(input)
    ) == pytest.approx(input)
    assert transmission_from_attenutation(
        attenuation_from_transmission(input)
    ) == pytest.approx(input)


# inauspicious:
@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object(), False])
def test_natural_log_of_transmission_from_attenuation_raises_error(bad_input):
    with pytest.raises(ValidationError):
        natural_log_of_transmission_from_attenuation(bad_input)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object(), False])
def test_transmission_from_attenutation_raises_error(bad_input):
    with pytest.raises(ValidationError):
        transmission_from_attenutation(bad_input)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object(), False])
def test_attenuation_from_transmission_raises_error(bad_input):
    with pytest.raises(ValidationError):
        attenuation_from_transmission(bad_input)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object(), False])
def test_attenuation_from_natural_log_of_transmission_raises_error(bad_input):
    with pytest.raises(ValidationError):
        attenuation_from_natural_log_of_transmission(bad_input)
