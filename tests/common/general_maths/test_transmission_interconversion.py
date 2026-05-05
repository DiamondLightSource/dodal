import math

import pytest

from dodal.common.general_maths import transmission_interconversion


# happy:
@pytest.mark.parametrize(
    "ln_t,result", [(-1, 1000), (0, 0), (-0.4367, 436.7), (-5.9017, 5901.7)]
)
def test_attenuation_from_natural_log_of_transmission(ln_t, result):
    assert transmission_interconversion.attenuation_from_natural_log_of_transmission(
        ln_t
    ) == pytest.approx(result)


@pytest.mark.parametrize(
    "transmission_as_fraction,result",
    [(1, 0), (0.37, 994.25227334), (0.871, 138.1133), (4.2e-4, 7775.2558)],
)
def test_attenuation_from_transmission(transmission_as_fraction, result):
    assert transmission_interconversion.attenuation_from_transmission(
        transmission_as_fraction
    ) == pytest.approx(result)


@pytest.mark.parametrize(
    "attenuation_bn,result",
    [(0, 0), (1e3, -1), (712.6, -0.7126), (8034.1, -8.0341)],
)
def test_natural_log_of_transmission_from_attenuation(attenuation_bn, result):
    assert transmission_interconversion.natural_log_of_transmission_from_attenuation(
        attenuation_bn
    ) == pytest.approx(result)


@pytest.mark.parametrize(
    "attenuation_bn,result",
    [(0, 1), (1e3, 0.3678794), (145.1, 0.8649358), (7221.9, 7.3041331435179e-4)],
)
def test_transmission_from_attenutation(attenuation_bn, result):
    assert transmission_interconversion.transmission_from_attenutation(
        attenuation_bn
    ) == pytest.approx(result)


# inauspicious:


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_attenuation_from_natural_log_of_transmission_errors(bad_input):
    with pytest.raises(TypeError):
        transmission_interconversion.attenuation_from_natural_log_of_transmission(
            bad_input
        )


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_attenuation_from_transmission_errors(bad_input):
    with pytest.raises(TypeError):
        transmission_interconversion.attenuation_from_transmission(bad_input)


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_natural_log_of_transmission_from_attenuation_errors(bad_input):
    with pytest.raises(TypeError):
        transmission_interconversion.natural_log_of_transmission_from_attenuation(
            bad_input
        )


@pytest.mark.parametrize("bad_input", ["a", [], None, math.sin, object()])
def test_transmission_from_attenutation_errors(bad_input):
    with pytest.raises(TypeError):
        transmission_interconversion.transmission_from_attenutation(bad_input)
