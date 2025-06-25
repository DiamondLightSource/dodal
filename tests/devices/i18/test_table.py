import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading, set_mock_value

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

    await assert_reading(
        table,
        {
            "table-y": partial_reading(0.0),
            "table-x": partial_reading(0.0),
            "table-theta": partial_reading(0.0),
            "table-z": partial_reading(0.0),
        },
    )

    # Call set to update the position
    set_mock_value(table.x.user_readback, 1.23)
    set_mock_value(table.y.user_readback, 4.56)

    await assert_reading(
        table,
        {
            "table-y": partial_reading(4.56),
            "table-x": partial_reading(1.23),
            "table-theta": partial_reading(0.0),
            "table-z": partial_reading(0),
        },
    )


async def test_setting_xyztheta_position_table(table: Table):
    """
    Test setting x and y positions on the Table using the ophyd_async mock tools.
    """
    await assert_reading(
        table,
        {
            "table-y": partial_reading(0.0),
            "table-x": partial_reading(0.0),
            "table-theta": partial_reading(0.0),
            "table-z": partial_reading(0.0),
        },
    )

    # Call set to update the position
    set_mock_value(table.x.user_readback, 1.23)
    set_mock_value(table.y.user_readback, 4.56)
    set_mock_value(table.z.user_readback, 7.89)
    set_mock_value(table.theta.user_readback, 10.11)

    await assert_reading(
        table,
        {
            "table-y": partial_reading(4.56),
            "table-x": partial_reading(1.23),
            "table-theta": partial_reading(10.11),
            "table-z": partial_reading(7.89),
        },
    )
