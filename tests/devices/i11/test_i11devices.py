import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.i11.cyberstar_blower import CyberstarBlower
from dodal.devices.i11.i11_robot import NX100Robot, RobotJobs, RobotSampleState
from dodal.devices.i11.spinner import Spinner


@pytest.fixture
async def i11_robot() -> NX100Robot:
    async with init_devices(mock=True):
        i11_robot = NX100Robot(prefix="BL11I-EA-ROBOT-01:")
    return i11_robot


@pytest.mark.parametrize(
    "state",
    [
        RobotSampleState.CAROSEL,
        RobotSampleState.ONGRIP,
        RobotSampleState.DIFF,
    ],
)
async def test_robot_set_when_on_grip_moves_to_position(
    i11_robot: NX100Robot, state
) -> None:
    set_mock_value(i11_robot.robot_sample_state, state)  # Set to state
    set_mock_value(i11_robot.job, RobotJobs.GRIPC)  # Set to GRIPC state

    await i11_robot.set(10)
    location = await i11_robot.locate()
    assert location["readback"] == 10


@pytest.mark.parametrize("value_to_set", [-1000, 9999])
async def test_robot_set_fails_when_value_out_of_range(
    i11_robot: NX100Robot, value_to_set: int
) -> None:
    with pytest.raises(ValueError):
        await i11_robot.set(value_to_set)  # Should raise ValueError for out of range


async def test_robot_set_when_already_at_location(i11_robot: NX100Robot) -> None:
    set_mock_value(i11_robot.current_sample_position, 10)  # Set pos to 10
    await i11_robot.set(10)  # shouldn't do anything since already at position
    assert await i11_robot.current_sample_position.get_value() == 10


async def test_robot_recover(i11_robot: NX100Robot) -> None:
    set_mock_value(i11_robot.job, RobotJobs.GRIPC)  # Set to ONGRIP state
    set_mock_value(i11_robot.err, True)  # Set to ERROR state

    await i11_robot.recover()

    assert await i11_robot.err.get_value() == 0
    assert await i11_robot.job.get_value() == RobotJobs.RECOVER


async def test_robot_stage(i11_robot: NX100Robot) -> None:
    set_mock_value(i11_robot.servo_on, False)  # Set to OFF state
    set_mock_value(i11_robot.hold, True)  # Set to hold state

    await i11_robot.stage()

    assert await i11_robot.servo_on.get_value() == 1
    assert await i11_robot.hold.get_value() == 0


async def test_robot_pause_resume(i11_robot: NX100Robot) -> None:
    set_mock_value(i11_robot.hold, False)  # Set to not hold state
    await i11_robot.pause()
    assert await i11_robot.hold.get_value() == 1

    set_mock_value(i11_robot.hold, True)  # Set to hold state
    await i11_robot.resume()
    assert await i11_robot.hold.get_value() == 0


@pytest.mark.parametrize(
    "state",
    [
        RobotSampleState.CAROSEL,
        RobotSampleState.ONGRIP,
        RobotSampleState.DIFF,
    ],
)
async def test_when_sample_state_clear_sample_tablein(
    i11_robot: NX100Robot, state
) -> None:
    set_mock_value(i11_robot.robot_sample_state, state)  # Set to not ongrip state

    await i11_robot.clear_sample(table_in=True)
    assert await i11_robot.job.get_value() == RobotJobs.TABLEIN


async def test_robot_clear_sample_when_sample_on_carousel(
    i11_robot: NX100Robot,
) -> None:
    set_mock_value(
        i11_robot.robot_sample_state, RobotSampleState.CAROSEL
    )  # Set to not ongrip state

    await i11_robot.clear_sample(table_in=False)
    assert await i11_robot.robot_sample_state.get_value() == RobotSampleState.CAROSEL


async def test_robot_clear_sample_when_sample_unknown(
    i11_robot: NX100Robot,
) -> None:
    set_mock_value(
        i11_robot.robot_sample_state, RobotSampleState.UNKNOWN
    )  # Set to not ongrip state

    await i11_robot.clear_sample(table_in=False)
    assert (
        not await i11_robot.robot_sample_state.get_value() == RobotSampleState.CAROSEL
    )


async def test_robot_load_sample_when_sample_unknown(i11_robot: NX100Robot) -> None:
    set_mock_value(
        i11_robot.robot_sample_state, RobotSampleState.UNKNOWN
    )  # Set to not ongrip state

    await i11_robot.load_sample(10)  # Load sample at position 10
    assert not await i11_robot.job.get_value() == RobotJobs.PLACED


async def test_robot_clear_load_when_state_is_invalid(i11_robot: NX100Robot) -> None:
    set_mock_value(i11_robot.robot_sample_state, 99)  # to invalid state
    with pytest.raises(ValueError):
        await i11_robot.load_sample(10)  # Load sample at position 10
    with pytest.raises(ValueError):
        await i11_robot.clear_sample(10)  # Load sample at position 10


async def test_when_robot_must_stop_and_success_false(
    i11_robot: NX100Robot,
) -> None:
    set_mock_value(
        i11_robot.robot_sample_state, RobotSampleState.ONGRIP
    )  # set to ongrip
    set_mock_value(i11_robot.hold, False)  # Set to not hold state
    await i11_robot.stop(success=False)

    assert await i11_robot.hold.get_value() == 0
    assert await i11_robot.job.get_value() == RobotJobs.TABLEIN


@pytest.fixture
async def i11_spinner() -> Spinner:
    async with init_devices(mock=True):
        i11_spinner = Spinner(prefix="BL11I-EA-SPIN-01:")
    return i11_spinner


async def test_spinner_pause_resume(i11_spinner: Spinner) -> None:
    await i11_spinner.pause()
    assert await i11_spinner.enable.get_value() == "Disabled"

    await i11_spinner.resume()
    assert await i11_spinner.enable.get_value() == "Enabled"


@pytest.fixture
async def i11_cyberstar() -> CyberstarBlower:
    async with init_devices(mock=True):
        i11_cyberstar = CyberstarBlower(
            prefix="BL11I-EA-BLOW-01:", update=True, autotune=True
        )
    return i11_cyberstar


async def test_blower_setpoint_and_locate(i11_cyberstar: CyberstarBlower) -> None:
    await i11_cyberstar.set(100.0)
    assert await i11_cyberstar.setpoint.get_value() == 100.0
    location = await i11_cyberstar.locate()
    assert location["setpoint"] == 100.0
