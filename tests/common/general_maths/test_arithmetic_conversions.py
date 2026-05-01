import pytest

from dodal.common.general_maths.arithmetic_conversions import (
    convert_cm_to_mm,
    convert_ev_to_kev,
    convert_factor_to_percentage,
    convert_microns_to_cm,
    convert_microns_to_mm,
    convert_mm_to_cm,
    convert_mm_to_microns,
    convert_percentage_to_factor,
)

# expected success tests (the 'Happy Path'):


@pytest.mark.parametrize("input,result", [(0.01, 1.0), (1.0, 100)])
def test_conversion_to_percentage_from_factor(input, result):
    assert convert_factor_to_percentage(f=input) == result


@pytest.mark.parametrize("input,result", [(1.0, 0.01), (100, 1.0)])
def test_conversion_to_factor_from_percentage(input, result):
    assert convert_percentage_to_factor(pc=input) == result


@pytest.mark.parametrize("input,result", [(10000, 1.0), (1000, 0.1)])
def test_conversion_from_microns_to_centimetres(input, result):
    assert convert_microns_to_cm(t_um=input) == result


@pytest.mark.parametrize("input,result", [(1000, 1.0), (10000, 10)])
def test_conversion_from_microns_to_millimeters(input, result):
    assert convert_microns_to_mm(v_um=input) == result


@pytest.mark.parametrize("input,result", [(1.0, 1000), (10, 10000)])
def test_conversion_from_millimeters_to_microns(input, result):
    assert convert_mm_to_microns(w_mm=input) == result


@pytest.mark.parametrize("input,result", [(1.0, 0.1), (100, 10)])
def test_conversion_from_millimetres_to_centimetres(input, result):
    assert convert_mm_to_cm(x_mm=input) == result


@pytest.mark.parametrize("input,result", [(1.0, 10), (0.1, 1)])
def test_conversion_from_centimetres_to_millimetres(input, result):
    assert convert_cm_to_mm(y_cm=input) == result


@pytest.mark.parametrize("input,result", [(1000, 1.0), (100, 0.1)])
def test_conversion_from_electronvolts_to_kiloelectronvolts(input, result):
    assert convert_ev_to_kev(energy_ev=input) == result
