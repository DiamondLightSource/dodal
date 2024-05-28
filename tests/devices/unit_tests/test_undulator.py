from unittest.mock import ANY

import pytest
from ophyd_async.core import (
    DeviceCollector,
    assert_configuration,
    assert_reading,
)

from dodal.devices.undulator import Undulator, UndulatorGapAccess


@pytest.fixture
async def undulator() -> Undulator:
    async with DeviceCollector(mock=True):
        undulator = Undulator(
            "UND-01",
            name="undulator",
            poles=80,
            length=2.0,
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
        )
    assert undulator.poles is None
    assert "undulator-poles" not in (await undulator.read_configuration())


async def test_length_not_propagated_if_not_supplied():
    async with DeviceCollector(mock=True):
        undulator = Undulator(
            "UND-01",
            name="undulator",
            poles=80,
        )
    assert undulator.length is None
    assert "undulator-length" not in (await undulator.read_configuration())
