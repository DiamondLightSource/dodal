import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.training_rig.sample_stage import TrainingRigSampleStage


@pytest.fixture
async def stage() -> TrainingRigSampleStage:
    async with init_devices(mock=True):
        stage = TrainingRigSampleStage(prefix="DEMO-STAGE-01:")

    return stage


async def test_reading_training_rig(stage: TrainingRigSampleStage):
    await assert_reading(
        stage,
        {
            "stage-theta": partial_reading(0.0),
            "stage-x": partial_reading(0.0),
        },
    )
