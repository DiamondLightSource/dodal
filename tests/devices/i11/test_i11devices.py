from unittest.mock import MagicMock, patch

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.eurotherm import UpdatingEurothermGeneral
from dodal.devices.i11.cyberstar_blower import AutotunedCyberstarBlower
from dodal.devices.i11.nx100robot import NX100Robot, RobotJobs, RobotSampleState
from dodal.devices.i11.spinner import Spinner


@pytest.fixture
async def i11_robot() -> NX100Robot:
    async with init_devices(mock=True):
        i11_robot = NX100Robot(prefix="BL11I-EA-ROBOT-01:")
    return i11_robot


@pytest.mark.parametrize(
    "state",
    [
        RobotSampleState.CAROUSEL,
        RobotSampleState.ONGRIP,
        RobotSampleState.DIFFRACTOMETER,
    ],
)
@pytest.mark.parametrize(
    "set_location",
    [10, 20, 30],
)
async def test_robot_set_moves_to_position(
    i11_robot: NX100Robot, state: RobotSampleState, set_location: int
) -> None:
    set_mock_value(i11_robot.current_sample_position, 10)  # Set initial position
    set_mock_value(i11_robot.robot_sample_state, state)  # Set to state

    await i11_robot.set(set_location)
    located_position = await i11_robot.locate()
    assert located_position["readback"] == set_location


@pytest.mark.parametrize("value_to_set", [-1000, 9999])
async def test_robot_set_fails_when_value_out_of_range(
    i11_robot: NX100Robot, value_to_set: int
) -> None:
    with pytest.raises(
        ValueError,
        match=f"Sample location must be between {i11_robot.MIN_NUMBER_OF_SAMPLES} and {i11_robot.MAX_NUMBER_OF_SAMPLES}, got {value_to_set}",
    ):
        await i11_robot.set(value_to_set)  # Should raise ValueError for out of range


@patch("dodal.devices.i11.nx100robot.LOGGER")
async def test_robot_set_when_already_at_location(
    patch_logger: MagicMock,
    i11_robot: NX100Robot,
):
    set_mock_value(i11_robot.current_sample_position, 10)  # Set pos to 10
    await i11_robot.set(10)  # shouldn't do anything since already at position
    assert await i11_robot.current_sample_position.get_value() == 10

    last_log = patch_logger.mock_calls[-1].args[0]

    assert "Robot already at position" in last_log


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
        RobotSampleState.CAROUSEL,
        RobotSampleState.ONGRIP,
        RobotSampleState.DIFFRACTOMETER,
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
        i11_robot.robot_sample_state, RobotSampleState.CAROUSEL
    )  # Set to not ongrip state

    await i11_robot.clear_sample(table_in=False)
    assert await i11_robot.robot_sample_state.get_value() == RobotSampleState.CAROUSEL


async def test_robot_clear_sample_when_sample_unknown(
    i11_robot: NX100Robot,
) -> None:
    set_mock_value(
        i11_robot.robot_sample_state, RobotSampleState.UNKNOWN
    )  # Set to not ongrip state

    await i11_robot.clear_sample(table_in=False)
    assert (
        not await i11_robot.robot_sample_state.get_value() == RobotSampleState.CAROUSEL
    )


async def test_robot_load_sample_when_sample_unknown(i11_robot: NX100Robot) -> None:
    set_mock_value(
        i11_robot.robot_sample_state, RobotSampleState.UNKNOWN
    )  # Set to not ongrip state

    await i11_robot.load_sample(10)  # Load sample at position 10
    assert not await i11_robot.job.get_value() == RobotJobs.PLACE_DIFFRACTOMETER


async def test_robot_clear_load_when_state_is_invalid(i11_robot: NX100Robot) -> None:
    set_mock_value(i11_robot.robot_sample_state, 99)  # to invalid state
    with pytest.raises(ValueError):
        await i11_robot.load_sample(10)  # Load sample at position 10 and fail
    with pytest.raises(ValueError):
        await i11_robot.clear_sample()  # clear sample and fail


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


async def test_spinner_pause_(i11_spinner: Spinner) -> None:
    await i11_spinner.pause()
    assert await i11_spinner.enable.get_value() == "Disabled"


async def test_spinner_resume(i11_spinner: Spinner) -> None:
    await i11_spinner.resume()
    assert await i11_spinner.enable.get_value() == "Enabled"


@pytest.fixture
async def i11_cyberstar() -> AutotunedCyberstarBlower:
    async with init_devices(mock=True):
        i11_cyberstar = AutotunedCyberstarBlower(
            prefix="BL11I-EA-BLOW-01:", controller_type=UpdatingEurothermGeneral
        )
    return i11_cyberstar


async def test_blower_setpoint_and_locate(
    i11_cyberstar: AutotunedCyberstarBlower,
) -> None:
    await i11_cyberstar.controller.set(100.0)
    assert await i11_cyberstar.controller.setpoint.get_value() == 100.0
    location = await i11_cyberstar.controller.locate()
    assert location["setpoint"] == 100.0
