from unittest.mock import ANY

import numpy as np
import pytest
from ophyd_async.core import DeviceCollector
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    set_mock_value,
)

from dodal.devices.undulator import (
    AccessError,
    Undulator,
    UndulatorGapAccess,
    _get_closest_gap_for_energy,
)

ID_GAP_LOOKUP_TABLE_PATH: str = (
    "./tests/devices/unit_tests/test_beamline_undulator_to_gap_lookup_table.txt"
)


@pytest.fixture
async def undulator() -> Undulator:
    async with DeviceCollector(mock=True):
        undulator = Undulator(
            "UND-01",
            name="undulator",
            poles=80,
            length=2.0,
            id_gap_lookup_table_path=ID_GAP_LOOKUP_TABLE_PATH,
        )
    return undulator


async def test_reading_includes_read_fields(undulator: Undulator):
    await assert_reading(
        undulator,
        {
            "undulator-gap_access": {
                "value": UndulatorGapAccess.ENABLED,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "undulator-gap_motor": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "undulator-current_gap": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
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
                "alarm_severity": ANY,
            },
            "undulator-gap_motor-velocity": {
                "value": 0.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "undulator-length": {
                "value": 2.0,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "undulator-poles": {
                "value": 80,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
            "undulator-gap_discrepancy_tolerance_mm": {
                "value": 0.002,
                "timestamp": ANY,
                "alarm_severity": ANY,
            },
        },
    )


async def test_poles_not_propagated_if_not_supplied():
    async with DeviceCollector(mock=True):
        undulator = Undulator(
            "UND-01",
            name="undulator",
            length=2.0,
            id_gap_lookup_table_path=ID_GAP_LOOKUP_TABLE_PATH,
        )
    assert undulator.poles is None
    assert "undulator-poles" not in (await undulator.read_configuration())


async def test_length_not_propagated_if_not_supplied():
    async with DeviceCollector(mock=True):
        undulator = Undulator(
            "UND-01",
            name="undulator",
            poles=80,
            id_gap_lookup_table_path=ID_GAP_LOOKUP_TABLE_PATH,
        )
    assert undulator.length is None
    assert "undulator-length" not in (await undulator.read_configuration())


@pytest.mark.parametrize(
    "energy, expected_output", [(5730, 5.4606), (7200, 6.045), (9000, 6.404)]
)
def test_correct_closest_distance_to_energy_from_table(energy, expected_output):
    energy_to_distance_table = np.array([[5700, 5.4606], [7000, 6.045], [9700, 6.404]])
    assert (
        _get_closest_gap_for_energy(energy, energy_to_distance_table) == expected_output
    )


async def test_when_gap_access_is_disabled_set_energy_then_error_is_raised(
    undulator,
):
    set_mock_value(undulator.gap_access, UndulatorGapAccess.DISABLED)
    with pytest.raises(AccessError):
        await undulator.set(5)
