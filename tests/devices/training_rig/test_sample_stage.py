from unittest import mock

import pytest
from ophyd_async.core import init_devices

from dodal.devices.training_rig.sample_stage import TrainingRigSampleStage


@pytest.fixture
async def stage() -> TrainingRigSampleStage:
    async with init_devices(mock=True):
        stage = TrainingRigSampleStage(prefix="DEMO-STAGE-01:")

    return stage


async def test_reading_training_rig(stage: TrainingRigSampleStage):
    reading = await stage.read()
    assert reading == {
        "stage-theta": {
            "alarm_severity": mock.ANY,
            "timestamp": mock.ANY,
            "value": 0.0,
        },
        "stage-x": {
            "alarm_severity": mock.ANY,
            "timestamp": mock.ANY,
            "value": 0.0,
        },
    }
