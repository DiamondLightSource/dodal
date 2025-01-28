from unittest.mock import ANY

import pytest
from ophyd_async.core import DeviceCollector
from ophyd_async.testing import set_mock_value

from dodal.devices.i18.table import Table, TablePosition


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
    set_mock_value(table.x.user_readback, 0.0)
    set_mock_value(table.y.user_readback, 0.0)

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

    # Create a position object
    position = TablePosition(x=1.23, y=4.56, z=0.0, theta=0.0)

    # Call set to update the position
    await table.set(position)

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
    set_mock_value(table.x.user_readback, 0.0)
    set_mock_value(table.y.user_readback, 0.0)
    set_mock_value(table.z.user_readback, 0.0)
    set_mock_value(table.theta.user_readback, 0.0)

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

    # Create a position object
    position = TablePosition(x=1.23, y=4.56, z=7.89, theta=10.11)

    # Call set to update the position
    await table.set(position)

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
