import pytest
from ophyd_async.core import DeviceCollector

from dodal.devices.i18.thor_labs_stage import ThorLabsStage, XYPosition


@pytest.fixture
async def fake_thor_labs_stage():
    async with DeviceCollector(mock=True):
        fake_thor_labs_stage = ThorLabsStage("", "thor_labs_stage")

    return fake_thor_labs_stage


async def test_setting(fake_thor_labs_stage: ThorLabsStage):
    pos = XYPosition(x=5, y=5)
    await fake_thor_labs_stage.set(pos)
