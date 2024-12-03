from ophyd_async.core import get_mock

from dodal.devices.aithre_lasershaping.robot import BartRobot


async def test_robot():
    robot = BartRobot(name="laserrobot", prefix="LA18L-MO-ROBOT-01:")
    await robot.connect(mock=True)
