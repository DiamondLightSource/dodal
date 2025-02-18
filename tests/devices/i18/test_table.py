from unittest.mock import ANY

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.i18.table import Table


@pytest.fixture
async def table() -> Table:
    """Fixture to set up a mock Table device using init_devices."""
    async with init_devices(mock=True):
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
    set_mock_value(table.x.user_readback, 1.23)
    set_mock_value(table.y.user_readback, 4.56)

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
    set_mock_value(table.x.user_readback, 1.23)
    set_mock_value(table.y.user_readback, 4.56)
    set_mock_value(table.z.user_readback, 7.89)
    set_mock_value(table.theta.user_readback, 10.11)

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
