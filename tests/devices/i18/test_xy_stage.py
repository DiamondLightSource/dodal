import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, set_mock_value

from dodal.devices.motors import XYStage


@pytest.fixture
async def stage():
    async with init_devices(mock=True):
        stage = XYStage("")

    return stage


async def test_setting(stage: XYStage):
    """
    Test setting x and y positions on the XYStage using ophyd_async mock tools.
    """

    await assert_reading(
        stage,
        {"stage-x": {"value": 0.0}, "stage-y": {"value": 0.0}},
    )

    # Call set to update the position
    set_mock_value(stage.x.user_readback, 5)
    set_mock_value(stage.y.user_readback, 5)

    await assert_reading(
        stage,
        {"stage-x": {"value": 5.0}, "stage-y": {"value": 5.0}},
    )
