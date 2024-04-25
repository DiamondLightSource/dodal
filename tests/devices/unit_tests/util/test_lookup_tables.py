import pytest
from pytest import mark

from dodal.devices.util.lookup_tables import (
    energy_distance_table,
    linear_interpolation_lut,
)


async def test_energy_to_distance_table_correct_format():
    table = await energy_distance_table(
        "./tests/devices/unit_tests/test_beamline_undulator_to_gap_lookup_table.txt"
    )
    assert table[0][0] == 5700
    assert table[49][1] == 6.264
    assert table.shape == (50, 2)


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
