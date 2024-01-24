import pytest
from pytest import mark

from dodal.devices.util.lookup_tables import (
    linear_interpolation_lut,
)


@mark.parametrize("s, expected_t", [(2.0, 1.0), (3.0, 1.5), (5.0, 4.0), (5.25, 6.0)])
def test_linear_interpolation(s, expected_t):
    lut_converter = linear_interpolation_lut(
        "tests/test_data/test_beamline_dcm_roll_converter.txt"
    )
    assert lut_converter(s) == expected_t


@mark.parametrize(
    "s, expected_t", [(2.0, 1.0), (3.0, 1.5), (5.0, 4.0), (5.25, 6.0), (5.5, 8.0)]
)
def test_linear_interpolation_reverse_order(s, expected_t):
    lut_converter = linear_interpolation_lut(
        "tests/test_data/test_beamline_dcm_roll_converter_reversed.txt"
    )
    actual_t = lut_converter(s)
    assert actual_t == expected_t, f"actual {actual_t} != expected {expected_t}"


@mark.parametrize("s", [(1.999,), (5.501,)])
def test_linear_interpolation_rejects_extrapolation(s):
    lut_converter = linear_interpolation_lut(
        "tests/test_data/test_beamline_dcm_roll_converter.txt"
    )
    with pytest.raises(ValueError):
        lut_converter(s)


def test_linear_interpolation_rejects_non_monotonic_increasing():
    with pytest.raises(AssertionError):
        linear_interpolation_lut(
            "tests/test_data/test_beamline_dcm_roll_converter_non_monotonic.txt"
        )
