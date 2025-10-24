import re

import pytest

from dodal.devices.i09_1_shared import calculate_gap_i09_hu, get_hu_lut_as_dict
from tests.devices.i09_1_shared.test_data import TEST_HARD_UNDULATOR_LUT


@pytest.fixture
async def lut_dictionary() -> dict:
    return await get_hu_lut_as_dict(TEST_HARD_UNDULATOR_LUT)


@pytest.mark.parametrize(
    "energy, order, expected_gap",
    [
        (2.13, 1, 12.81),
        (2.78, 3, 6.05),
        (6.24, 5, 7.95),
    ],
)
async def test_calculate_gap_from_energy(
    energy: float,
    order: int,
    expected_gap: float,
    lut_dictionary: dict,
):
    assert calculate_gap_i09_hu(energy, lut_dictionary, order) == pytest.approx(
        expected_gap, abs=0.01
    )


async def test_calculate_gap_from_energy_wrong_order(
    lut_dictionary: dict,
):
    wrong_order = 100
    with pytest.raises(
        ValueError,
        match=re.escape(f"Order parameter {wrong_order} not found in lookup table"),
    ):
        calculate_gap_i09_hu(30, lut_dictionary, wrong_order)


async def test_calculate_gap_from_energy_wrong_k(
    lut_dictionary: dict,
):
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Diffraction parameter squared must be positive! Calculated value -1.78"
        ),
    ):
        calculate_gap_i09_hu(30, lut_dictionary, 1)
