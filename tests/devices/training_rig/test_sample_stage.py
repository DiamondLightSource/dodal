import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading

from dodal.devices.motors import XThetaStage


@pytest.fixture
async def stage() -> XThetaStage:
    async with init_devices(mock=True):
        stage = XThetaStage(prefix="DEMO-STAGE-01:")

    return stage


async def test_reading_training_rig(stage: XThetaStage):
    await assert_reading(
        stage,
        {
            "stage-theta": {
                "value": 0.0,
            },
            "stage-x": {
                "value": 0.0,
            },
        },
    )
