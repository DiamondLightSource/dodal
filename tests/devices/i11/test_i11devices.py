import pytest

# from ophyd_async.testing import set_mock_value
# from dodal.common.beamlines.beamline_utils import (
#     get_path_provider,
# )
from dodal.devices.i11.i11_robot import I11Robot

# def test_mythen3_prepare(RE: RunEngine, mythen3: Mythen3):
#     def _inner_prepare(mythen3: Mythen3):
#         m = mythen3()
#         yield from bps.prepare(m)

#     RE(_inner_prepare(mythen3))


@pytest.fixture
async def test_robot() -> None:
    robot = I11Robot(prefix="BL11I-EA-ROBOT-01:")
    await robot.connect(mock=True)

    await robot.start_robot()
    await robot.load_sample(10)
    location = await robot.locate()
    assert location["readback"] == 10
