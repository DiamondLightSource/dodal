import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.i11.cyberstar_blower import CyberstarBlower
from dodal.devices.i11.i11_robot import NX100Robot, RobotJobs
from dodal.devices.i11.spinner import Spinner


@pytest.fixture
async def i11_robot() -> NX100Robot:
    async with init_devices(mock=True):
        i11_robot = NX100Robot(prefix="BL11I-EA-ROBOT-01:")
    return i11_robot


async def test_robot_moves_to_position(i11_robot: NX100Robot):
    set_mock_value(i11_robot.robot_sample_state, 1.0)  # Set to CAROSEL state
    set_mock_value(i11_robot.job, RobotJobs.GRIPC)  # Set to CAROSEL state

    await i11_robot.set(10)
    location = await i11_robot.locate()
    assert location["readback"] == 10


@pytest.fixture
async def i11_spinner() -> Spinner:
    async with init_devices(mock=True):
        i11_spinner = Spinner(prefix="BL11I-EA-SPIN-01:")
    return i11_spinner


async def test_spinner_pause_resume(i11_spinner: Spinner):
    await i11_spinner.pause()
    assert await i11_spinner.enable.get_value() == "Disabled"

    await i11_spinner.resume()
    assert await i11_spinner.enable.get_value() == "Enabled"


async def test_robot(i11_robot: NX100Robot):
    set_mock_value(i11_robot.robot_sample_state, 1.0)  # Set to CAROSEL state
    set_mock_value(i11_robot.job, RobotJobs.GRIPC)  # Set to CAROSEL state

    await i11_robot.set(10)
    location = await i11_robot.locate()
    assert location["readback"] == 10


@pytest.fixture
async def i11_cyberstar() -> CyberstarBlower:
    async with init_devices(mock=True):
        i11_cyberstar = CyberstarBlower(prefix="BL11I-EA-BLOW-01:")
    return i11_cyberstar


# async def test_blower(i11_cyberstar: CyberstarBlower):
#     return blower
