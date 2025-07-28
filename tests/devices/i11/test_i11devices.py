from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.i11.cyberstar_blower import CyberstarBlower
from dodal.devices.i11.i11_robot import NX100Robot, RobotJobs


async def test_robot():
    with init_devices(mock=True):
        # Initialize the robot with a mock connection
        robot = NX100Robot(prefix="BL11I-EA-ROBOT-01:")

    set_mock_value(robot.robot_sample_state, 1.0)  # Set to CAROSEL state
    set_mock_value(robot.job, RobotJobs.GRIPC)  # Set to CAROSEL state

    await robot.set(10)
    location = await robot.locate()
    assert location["readback"] == 10


async def test_blower():
    with init_devices(mock=True):
        blower = CyberstarBlower(
            prefix="BL11I-EA-BLOW-02:", infix="LOOP1:", autotune=True, update=True
        )

    return blower
