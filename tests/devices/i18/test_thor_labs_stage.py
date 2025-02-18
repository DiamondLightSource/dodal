from unittest.mock import ANY

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.i18.thor_labs_stage import ThorLabsStage


@pytest.fixture
async def thor_labs_stage():
    async with init_devices(mock=True):
        thor_labs_stage = ThorLabsStage("")

    return thor_labs_stage


async def test_setting(thor_labs_stage: ThorLabsStage):
    """
    Test setting x and y positions on the ThorLabsStage using ophyd_async mock tools.
    """

    reading = await thor_labs_stage.read()

    expected_reading = {
        "thor_labs_stage-x": {
            "value": 0.0,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "thor_labs_stage-y": {
            "value": 0.0,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
    }

    assert reading == expected_reading

    # Call set to update the position
    set_mock_value(thor_labs_stage.x.user_readback, 5)
    set_mock_value(thor_labs_stage.y.user_readback, 5)

    # Read the stage's current position
    reading = await thor_labs_stage.read()

    # Define the expected position values after the set operation
    expected_reading = {
        "thor_labs_stage-x": {
            "value": 5.0,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
        "thor_labs_stage-y": {
            "value": 5.0,
            "timestamp": ANY,
            "alarm_severity": 0,
        },
    }

    # Assert the actual reading matches the expected reading
    assert reading == expected_reading
