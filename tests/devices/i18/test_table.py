from unittest.mock import ANY

import pytest
from ophyd_async.core import DeviceCollector

from dodal.devices.i18.table import Table


@pytest.fixture
async def table() -> Table:
    """Fixture to set up a mock Table device using DeviceCollector."""
    async with DeviceCollector(mock=True):
        table = Table(prefix="MIRROR:")
    return table


async def test_setting_xy_position_table(table: Table):
    """
    Test setting x and y positions on the Table using the ophyd_async mock tools.
    """

    reading = await table.read()
    expected_reading = {
        "table-y": {
            "value": 0.0,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "table-x": {
            "value": 0.0,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "table-theta": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "table-z": {"alarm_severity": 0, "timestamp": ANY, "value": 0.0},
    }

    assert reading == expected_reading

    # Call set to update the position
    await table.x.set(1.23)
    await table.y.set(4.56)

    reading = await table.read()
    expected_reading = {
        "table-y": {
            "value": 4.56,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "table-x": {
            "value": 1.23,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "table-theta": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "table-z": {"alarm_severity": 0, "timestamp": ANY, "value": 0.0},
    }

    assert reading == expected_reading


async def test_setting_xyztheta_position_table(table: Table):
    """
    Test setting x and y positions on the Table using the ophyd_async mock tools.
    """
    reading = await table.read()
    expected_reading = {
        "table-y": {
            "value": 0.0,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "table-x": {
            "value": 0.0,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "table-theta": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 0.0,
        },
        "table-z": {"alarm_severity": 0, "timestamp": ANY, "value": 0.0},
    }

    assert reading == expected_reading

    # Call set to update the position
    await table.x.set(1.23)
    await table.y.set(4.56)
    await table.z.set(7.89)
    await table.theta.set(10.11)

    reading = await table.read()
    expected_reading = {
        "table-y": {
            "value": 4.56,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "table-x": {
            "value": 1.23,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "table-theta": {
            "alarm_severity": 0,
            "timestamp": ANY,
            "value": 10.11,
        },
        "table-z": {"alarm_severity": 0, "timestamp": ANY, "value": 7.89},
    }

    assert reading == expected_reading
