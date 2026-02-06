import re
from unittest.mock import patch

import pytest
from daq_config_server.client import ConfigServer

from dodal.devices.beamlines.i09_1_shared import calculate_gap_i09_hu
from dodal.devices.beamlines.i09_1_shared.hard_undulator_functions import (
    I09HardLutProvider,
    calculate_energy_i09_hu,
)

pytest_plugins = ["dodal.testing.fixtures.devices.hard_undulator"]


@pytest.fixture()
def lut_provider(
    mock_config_client: ConfigServer,
) -> I09HardLutProvider:
    return I09HardLutProvider(mock_config_client, "path/to/lut")


@pytest.mark.parametrize(
    "energy, order, expected_gap",
    [
        (2.13, 1, 12.8146),
        (2.78, 3, 6.0537),
        (6.24, 5, 7.9561),
    ],
)
async def test_calculate_gap_from_energy(
    energy: float,
    order: int,
    expected_gap: float,
    lut_provider: I09HardLutProvider,
):
    assert calculate_gap_i09_hu(lut_provider, energy, order) == pytest.approx(
        expected_gap, abs=0.0001
    )


@pytest.mark.parametrize(
    "energy, order, gap",
    [
        (2.1454, 1, 12.91),
        (2.6410, 3, 5.75),
        (6.1355, 5, 7.84),
    ],
)
async def test_calculate_energy_from_gap(
    energy: float,
    order: int,
    gap: float,
    lut_provider: I09HardLutProvider,
):
    assert calculate_energy_i09_hu(lut_provider, gap, order) == pytest.approx(
        energy, abs=0.0001
    )


async def test_calculate_gap_from_energy_wrong_order(
    lut_provider: I09HardLutProvider,
):
    wrong_order = 100
    with pytest.raises(
        ValueError,
        match=re.escape(f"Order parameter {wrong_order} not found in lookup table"),
    ):
        calculate_gap_i09_hu(lut_provider, 30, wrong_order)


async def test_calculate_gap_from_energy_wrong_energy(
    lut_provider: I09HardLutProvider,
):
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Requested energy 30 keV is out of range for harmonic 1: [2.12, 3.05] keV"
        ),
    ):
        calculate_gap_i09_hu(lut_provider, 30, 1)


@patch(
    "dodal.devices.i09_1_shared.hard_undulator_functions._validate_energy_in_range",
    autospec=True,
)
async def test_calculate_gap_from_energy_wrong_k(
    validate_energy_in_range_mock,
    lut_provider: I09HardLutProvider,
):
    with pytest.raises(
        ValueError,
        match=re.escape(
            "Diffraction parameter squared must be positive! Calculated value -1.78"
        ),
    ):
        calculate_gap_i09_hu(lut_provider, 30, 1)
