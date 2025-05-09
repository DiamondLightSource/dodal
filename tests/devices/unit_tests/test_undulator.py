from unittest.mock import ANY

import numpy as np
import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    set_mock_value,
)

from dodal.devices.undulator import (
    AccessError,
    Undulator,
    UndulatorGapAccess,
    _get_gap_for_energy,
)
from tests.constants import UNDULATOR_ID_GAP_LOOKUP_TABLE_PATH


@pytest.fixture
async def undulator(RE) -> Undulator:
    async with init_devices(mock=True):
        undulator = Undulator(
            "UND-01",
            name="undulator",
            poles=80,
            length=2.0,
            id_gap_lookup_table_path=UNDULATOR_ID_GAP_LOOKUP_TABLE_PATH,
        )
    return undulator


async def test_reading_includes_read_fields(undulator: Undulator):
    await assert_reading(
        undulator,
        {
            "undulator-gap_access": {
                "value": UndulatorGapAccess.ENABLED,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "undulator-gap_motor": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "undulator-current_gap": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )


async def test_configuration_includes_configuration_fields(undulator: Undulator):
    await assert_configuration(
        undulator,
        {
            "undulator-gap_motor-motor_egu": {
                "value": "",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "undulator-gap_motor-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "undulator-length": {
                "value": 2.0,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "undulator-poles": {
                "value": 80,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "undulator-gap_discrepancy_tolerance_mm": {
                "value": 0.002,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "undulator-gap_motor-offset": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
        },
    )


async def test_poles_not_propagated_if_not_supplied():
    async with init_devices(mock=True):
        undulator = Undulator(
            "UND-01",
            name="undulator",
            length=2.0,
            id_gap_lookup_table_path=UNDULATOR_ID_GAP_LOOKUP_TABLE_PATH,
        )
    assert undulator.poles is None
    assert "undulator-poles" not in (await undulator.read_configuration())


async def test_length_not_propagated_if_not_supplied():
    async with init_devices(mock=True):
        undulator = Undulator(
            "UND-01",
            name="undulator",
            poles=80,
            id_gap_lookup_table_path=UNDULATOR_ID_GAP_LOOKUP_TABLE_PATH,
        )
    assert undulator.length is None
    assert "undulator-length" not in (await undulator.read_configuration())


@pytest.mark.parametrize(
    "energy, expected_output",
    [(0, 10), (5, 55), (20, 160), (36, 100), (39, 250)],
)
def test_correct_closest_distance_to_energy_from_table(energy, expected_output):
    energy_to_distance_table = np.array(
        [[0, 10], [10, 100], [35, 250], [35, 50], [40, 300]]
    )
    assert _get_gap_for_energy(energy, energy_to_distance_table) == expected_output


async def test_when_gap_access_is_disabled_set_energy_then_error_is_raised(
    undulator,
):
    set_mock_value(undulator.gap_access, UndulatorGapAccess.DISABLED)
    with pytest.raises(AccessError):
        await undulator.set(5)
