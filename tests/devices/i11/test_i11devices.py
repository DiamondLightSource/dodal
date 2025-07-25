import pytest

from dodal.devices.i11.cyberstar_blower import CyberstarBlower
from dodal.devices.i11.i11_robot import I11Robot


@pytest.fixture
async def test_robot() -> None:
    robot = I11Robot(prefix="BL11I-EA-ROBOT-01:")
    await robot.connect(mock=True)

    await robot.start_robot()
    await robot.load_sample(10)
    location = await robot.locate()
    assert location["readback"] == 10


@pytest.fixture
async def test_blower() -> None:
    blower = CyberstarBlower(
        prefix="BL11I-EA-BLOW-02:", infix="LOOP1:", autotune=True, update=True
    )
    await blower.connect(mock=True)
