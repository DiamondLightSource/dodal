import pytest

from dodal.devices.i16.mecarobot import CartesianSpace, Meca500


async def test_meca500_derived_signals():
    robot = Meca500("")
    await robot.connect(mock=True)
    await robot.set(CartesianSpace(x=0.0, y=0, z=0.308, alpha=180, beta=90, gamma=0))

    # Move x to achieve robot's zero position (i.e., all joints are 0°)
    await robot.x.set(0.190)

    # Read joint positions
    joint_values = await robot.read()

    # Check that all joints are approximately 0°
    for reading in joint_values.values():
        assert pytest.approx(reading["value"], abs=1e-4) == 0

    # Check that setting joint angle correctly recalculates derived axes
    await robot.joints[0].set(90)
    assert pytest.approx(await robot.y.get_value(), abs=1e-4) == 0.190
    assert pytest.approx(await robot.x.get_value(), abs=1e-4) == 0
