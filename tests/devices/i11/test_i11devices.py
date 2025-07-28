from ophyd_async.testing import set_mock_value

from dodal.devices.i11.cyberstar_blower import CyberstarBlower
from dodal.devices.i11.i11_robot import NX100Robot, RobotJobs


async def test_robot():
    robot = NX100Robot(prefix="BL11I-EA-ROBOT-01:")
    await robot.connect(mock=True)

    set_mock_value(robot.robot_sample_state, 1.0)  # Set to CAROSEL state
    set_mock_value(robot.job, RobotJobs.GRIPC)  # Set to CAROSEL state

    await robot.set(10)
    location = await robot.locate()
    assert location["readback"] == 10


async def test_blower() -> None:
    blower = CyberstarBlower(
        prefix="BL11I-EA-BLOW-02:", infix="LOOP1:", autotune=True, update=True
    )
    await blower.connect(mock=True)
