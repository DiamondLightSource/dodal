import pytest
from pytest import mark

from dodal.devices.util.lookup_tables import (
    energy_distance_table,
    linear_extrapolation_lut,
    linear_interpolation_lut,
    parse_lookup_table,
)

TEST_DCM_LUT = "tests/test_data/test_beamline_dcm_roll_converter.txt"
TEST_DCM_LUT_REVERSED = "tests/test_data/test_beamline_dcm_roll_converter_reversed.txt"
TEST_BAD_DCM_LUT = "tests/test_data/test_beamline_dcm_roll_converter_non_monotonic.txt"
TEST_DET_DIST_CONVERTER_LUT = "tests/test_data/test_det_dist_converter.txt"


async def test_energy_to_distance_table_correct_format():
    table = await energy_distance_table(
        "./tests/devices/unit_tests/test_beamline_undulator_to_gap_lookup_table.txt"
    )
    assert table[0][0] == 5700
    assert table[49][1] == 6.264
    assert table.shape == (50, 2)


@mark.parametrize(
    "lut_path, num_columns", [(TEST_DCM_LUT, 2), (TEST_DET_DIST_CONVERTER_LUT, 3)]
)
def test_parse_lookup_table_returns_list_of_the_same_length_as_num_of_columns(
    lut_path, num_columns
):
    lut_values = parse_lookup_table(lut_path)

    assert isinstance(lut_values, list) and len(lut_values) == num_columns


@mark.parametrize("s, expected_t", [(2.0, 1.0), (3.0, 1.5), (5.0, 4.0), (5.25, 6.0)])
def test_linear_interpolation(s, expected_t):
    lut_converter = linear_interpolation_lut(*parse_lookup_table(TEST_DCM_LUT))
    assert lut_converter(s) == expected_t


@mark.parametrize(
    "s, expected_t", [(2.0, 1.0), (3.0, 1.5), (5.0, 4.0), (5.25, 6.0), (5.5, 8.0)]
)
def test_linear_extrapolation_interpolates(s, expected_t):
    lut_converter = linear_extrapolation_lut(*parse_lookup_table(TEST_DCM_LUT))
    assert lut_converter(s) == expected_t


@mark.parametrize("s, expected_t", [(1.0, 0.5), (6.0, 12), (0.5, 0.25), (5.75, 10)])
def test_linear_extrapolation_extrapolates(s, expected_t):
    lut_converter = linear_extrapolation_lut(*parse_lookup_table(TEST_DCM_LUT))
    assert lut_converter(s) == expected_t


@mark.parametrize(
    "s, expected_t", [(2.0, 1.0), (3.0, 1.5), (5.0, 4.0), (5.25, 6.0), (5.5, 8.0)]
)
def test_linear_interpolation_reverse_order(s, expected_t):
    lut_converter = linear_interpolation_lut(*parse_lookup_table(TEST_DCM_LUT_REVERSED))
    actual_t = lut_converter(s)
    assert actual_t == expected_t, f"actual {actual_t} != expected {expected_t}"


@mark.parametrize("s, expected_t", [(1.0, 1.0), (7.0, 8.0)])
def test_linear_interpolation_extrapolates_returning_the_last_value(s, expected_t):
    lut_converter = linear_interpolation_lut(*parse_lookup_table(TEST_DCM_LUT))
    actual_t = lut_converter(s)
    assert actual_t == expected_t, f"actual {actual_t} != expected {expected_t}"


def test_linear_interpolation_rejects_non_monotonic_increasing():
    test_s, test_t = parse_lookup_table(TEST_BAD_DCM_LUT)
    with pytest.raises(AssertionError):
        linear_interpolation_lut(test_s, test_t)
