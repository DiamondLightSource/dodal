import asyncio
import traceback
from asyncio import Event, create_task
from collections.abc import Callable
from functools import partial
from unittest.mock import ANY, AsyncMock, MagicMock, call, patch

import pytest
from ophyd_async.core import (
    callback_on_mock_put,
    get_mock,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.robot import (
    SAMPLE_LOCATION_EMPTY,
    WAIT_FOR_BEAMLINE_DISABLE_MSG,
    WAIT_FOR_BEAMLINE_ENABLE_MSG,
    BartRobot,
    BeamlineStatus,
    ControllerErrorCode,
    PinMounted,
    ProgErrorCode,
    RobotLoadError,
    SampleLocation,
)


@pytest.fixture
async def robot_for_unload():
    device = BartRobot("robot", "-MO-ROBOT-01:")
    device.NOT_BUSY_TIMEOUT = 0.3  # type: ignore
    device.LOAD_TIMEOUT = 0.3  # type: ignore
    await device.connect(mock=True)

    trigger_complete = Event()
    drying_complete = Event()

    async def finish_later():
        await drying_complete.wait()
        await asyncio.sleep(0.1)
        set_mock_value(device.program_running, False)
        set_mock_value(device.beamline_disabled, BeamlineStatus.ENABLED.value)

    async def fake_unload(*args, **kwargs):
        set_mock_value(device.program_running, True)
        set_mock_value(device.beamline_disabled, BeamlineStatus.DISABLED.value)
        await trigger_complete.wait()
        asyncio.create_task(finish_later())

    get_mock_put(device.unload).side_effect = fake_unload
    callback_on_mock_put(device.reset, partial(clear_errors, device))
    return device, trigger_complete, drying_complete


# Use log info messages to determine when to set the beamline enable, so we don't have to use any sleeps during testing
@pytest.fixture()
async def robot_for_load(bart_robot: BartRobot):
    sample_location = SampleLocation(15, 10)
    set_mock_value(bart_robot.beamline_disabled, BeamlineStatus.ENABLED.value)

    def _enable_beamline_and_update_pin(device: BartRobot):
        _beamline_enable(device)
        _set_pin_and_puck(sample_location, device)

    with patch("dodal.devices.robot.LOGGER.info") as mock_log_info:
        mock_log_info.side_effect = partial(
            _set_beamline_enabled_on_log_messages,
            bart_robot,
            _enable_beamline_and_update_pin,
            _beamline_disable,
        )
        yield bart_robot


@pytest.fixture()
async def robot_for_load_with_prog_error(
    robot_for_load: BartRobot,
):
    device = robot_for_load
    with patch("dodal.devices.robot.LOGGER.info") as mock_log_info:
        mock_log_info.side_effect = partial(_prog_error_on_unload_log_messages, device)
        yield device


@pytest.fixture()
async def robot_for_load_with_controller_error(
    robot_for_load: BartRobot,
):
    device = robot_for_load
    with patch("dodal.devices.robot.LOGGER.info") as mock_log_info:
        mock_log_info.side_effect = partial(
            _controller_error_on_unload_log_messages, device
        )
        yield device


def clear_errors(device: BartRobot, *args, **kwargs):
    set_mock_value(device.controller_error.code, 0)
    set_mock_value(device.prog_error.code, 0)


@pytest.fixture
async def bart_robot() -> BartRobot:
    device = BartRobot("robot", "-MO-ROBOT-01:")
    device.NOT_BUSY_TIMEOUT = 0.3  # type: ignore
    device.LOAD_TIMEOUT = 0.3  # type: ignore
    await device.connect(mock=True)
    set_mock_value(device.program_running, False)
    callback_on_mock_put(device.reset, partial(clear_errors, device))
    return device


# For tests which are intentionally triggering a timeout error
def _set_fast_robot_timeouts(robot: BartRobot):
    robot.LOAD_TIMEOUT = 0.01  # type: ignore
    robot.NOT_BUSY_TIMEOUT = 0.01  # type: ignore


async def test_given_robot_load_times_out_when_load_called_then_exception_contains_error_info(
    robot_with_late_error: BartRobot,
):
    device = robot_with_late_error

    with pytest.raises(RobotLoadError) as e:
        await device.set(SampleLocation(0, 0))
    assert e.value.error_code == EXPECTED_ERROR_CODE
    assert e.value.error_string == EXPECTED_ERROR_STRING
    assert str(e.value) == EXPECTED_ERROR_STRING


@patch("dodal.devices.robot.LOGGER")
async def test_given_program_running_when_load_pin_then_logs_the_program_name_and_times_out(
    patch_logger: MagicMock, bart_robot: BartRobot
):
    device = bart_robot
    _set_fast_robot_timeouts(device)
    program_name = "BAD_PROGRAM"
    set_mock_value(device.program_running, True)
    set_mock_value(device.program_name, program_name)
    with pytest.raises(RobotLoadError):
        await device.set(SampleLocation(0, 0))
    last_log = patch_logger.mock_calls[1].args[0]
    assert program_name in last_log


@patch("dodal.devices.robot.LOGGER")
async def test_given_program_not_running_but_pin_not_unmounting_when_load_pin_then_timeout(
    patch_logger: MagicMock, bart_robot: BartRobot
):
    device = bart_robot
    _set_fast_robot_timeouts(device)
    set_mock_value(device.gonio_pin_sensor, PinMounted.PIN_MOUNTED)
    device.load = AsyncMock(side_effect=device.load)
    with pytest.raises(RobotLoadError):
        await device.set(SampleLocation(15, 10))
    device.load.trigger.assert_called_once()  # type:ignore
    last_log = patch_logger.mock_calls[1].args[0]
    assert WAIT_FOR_BEAMLINE_DISABLE_MSG in last_log


@patch("dodal.devices.robot.LOGGER")
async def test_given_program_not_running_and_pin_unmounting_but_new_pin_not_mounting_when_load_pin_then_timeout(
    patch_logger: MagicMock,
    bart_robot: BartRobot,
):
    device = bart_robot
    _set_fast_robot_timeouts(device)
    set_mock_value(device.gonio_pin_sensor, PinMounted.NO_PIN_MOUNTED)
    device.load = AsyncMock(side_effect=device.load)
    with pytest.raises(RobotLoadError) as exc_info:
        await device.set(SampleLocation(15, 10))

    try:
        device.load.trigger.assert_called_once()  # type:ignore
        last_log = patch_logger.mock_calls[1].args[0]
        assert WAIT_FOR_BEAMLINE_DISABLE_MSG in last_log
    except AssertionError:
        traceback.print_exception(exc_info.value)
        raise


def _beamline_enable(device: BartRobot):
    set_mock_value(device.beamline_disabled, BeamlineStatus.ENABLED.value)


def _beamline_disable(device: BartRobot):
    set_mock_value(device.beamline_disabled, BeamlineStatus.DISABLED.value)


def _set_pin_and_puck(sample_location: SampleLocation, device: BartRobot):
    set_mock_value(device.current_puck, sample_location.puck)
    set_mock_value(device.current_pin, sample_location.pin)


def _set_beamline_enabled_on_log_messages(
    device: BartRobot,
    on_beamline_enable: Callable[[BartRobot], None],
    on_beamline_disable: Callable[[BartRobot], None],
    msg: str,
):
    if msg == WAIT_FOR_BEAMLINE_DISABLE_MSG:
        on_beamline_disable(device)
    elif msg == WAIT_FOR_BEAMLINE_ENABLE_MSG:
        on_beamline_enable(device)


def _prog_error_on_unload_log_messages(device: BartRobot, msg: str):
    if msg == WAIT_FOR_BEAMLINE_DISABLE_MSG:
        set_mock_value(device.prog_error.code, ProgErrorCode.SAMPLE_POSITION_NOT_READY)
        set_mock_value(device.prog_error.str, "Test error")


def _controller_error_on_unload_log_messages(device: BartRobot, msg: str):
    if msg == WAIT_FOR_BEAMLINE_DISABLE_MSG:
        set_mock_value(
            device.prog_error.code, ControllerErrorCode.LIGHT_CURTAIN_TRIPPED
        )
        set_mock_value(device.prog_error.str, "Test error")


@pytest.fixture
async def robot_with_early_error(
    bart_robot: BartRobot,
):
    """Mocks the logic that the robot would do on a successful load."""
    with patch("dodal.devices.robot.LOGGER.info") as mock_log_info:
        mock_log_info.side_effect = partial(
            _prog_error_on_unload_log_messages, bart_robot
        )
        set_mock_value(bart_robot.beamline_disabled, BeamlineStatus.ENABLED.value)
        yield bart_robot


@pytest.fixture
def robot_which_never_reports_new_pin(bart_robot: BartRobot):
    with patch("dodal.devices.robot.LOGGER.info") as mock_log_info:
        set_mock_value(bart_robot.beamline_disabled, BeamlineStatus.ENABLED.value)
        mock_log_info.side_effect = partial(
            _set_beamline_enabled_on_log_messages,
            bart_robot,
            _beamline_enable,
            _beamline_disable,
        )
        yield bart_robot


EXPECTED_ERROR_CODE = 10
EXPECTED_ERROR_STRING = "BAD"


@pytest.fixture
def robot_with_late_error(bart_robot: BartRobot):
    _set_fast_robot_timeouts(bart_robot)
    bart_robot._load_pin_and_puck = AsyncMock(side_effect=TimeoutError)

    set_mock_value(bart_robot.prog_error.code, EXPECTED_ERROR_CODE)
    set_mock_value(bart_robot.prog_error.str, EXPECTED_ERROR_STRING)
    with patch("dodal.devices.robot.LOGGER.info") as mock_log_info:
        set_mock_value(bart_robot.beamline_disabled, BeamlineStatus.ENABLED.value)
        mock_log_info.side_effect = partial(
            _set_beamline_enabled_on_log_messages,
            bart_robot,
            _beamline_enable,
            _beamline_disable,
        )
        yield bart_robot


async def test_given_program_not_running_and_pin_unmounts_then_mounts_when_load_pin_then_pin_loaded(
    robot_for_load: BartRobot,
):
    device = robot_for_load
    status = device.set(SampleLocation(15, 10))
    await status
    assert status.success
    assert (await device.next_puck.get_value()) == 15
    assert (await device.next_pin.get_value()) == 10
    get_mock_put(device.load).assert_called_once()


async def test_waiting_for_beamline_status_raises_error_when_prog_error(
    bart_robot: BartRobot,
):
    device = bart_robot
    set_mock_value(device.prog_error.code, 25)
    set_mock_value(device.beamline_disabled, BeamlineStatus.DISABLED.value)
    status = device.beamline_status_or_error(BeamlineStatus.ENABLED)
    with pytest.raises(RobotLoadError):
        await status


async def test_waiting_for_beamline_status_raises_error_when_controller_error(
    bart_robot: BartRobot,
):
    device = bart_robot
    set_mock_value(device.controller_error.code, 25)
    set_mock_value(device.beamline_disabled, BeamlineStatus.DISABLED.value)
    status = device.beamline_status_or_error(BeamlineStatus.ENABLED)
    with pytest.raises(RobotLoadError):
        await status


async def test_given_waiting_for_beamline_to_enable_when_beamline_enabled_then_no_error_raised(
    bart_robot: BartRobot,
):
    device = bart_robot
    status = create_task(device.beamline_status_or_error(BeamlineStatus.ENABLED))
    set_mock_value(device.beamline_disabled, BeamlineStatus.ENABLED.value)
    await status


async def test_robot_load_fails_if_new_puck_and_pin_not_reported(
    robot_which_never_reports_new_pin: BartRobot,
):
    robot = robot_which_never_reports_new_pin
    with pytest.raises(RobotLoadError, match="Robot timed out"):
        await robot.set(SampleLocation(15, 10))


@patch("dodal.devices.robot.wait_for")
async def test_set_waits_for_both_timeouts(
    mock_wait_for: AsyncMock, bart_robot: BartRobot
):
    device = bart_robot
    _set_fast_robot_timeouts(device)
    device._load_pin_and_puck = MagicMock()  # type: ignore
    await device.set(SampleLocation(1, 2))
    mock_wait_for.assert_awaited_once_with(ANY, timeout=0.02)


@pytest.mark.parametrize(
    "sample_location", [SAMPLE_LOCATION_EMPTY, SampleLocation(1, 2)]
)
async def test_moving_the_robot_will_reset_controller_error_and_throw_if_error_not_cleared(
    sample_location: SampleLocation, bart_robot: BartRobot
):
    device = bart_robot
    _set_fast_robot_timeouts(device)
    set_mock_value(
        device.controller_error.code, ControllerErrorCode.LIGHT_CURTAIN_TRIPPED.value
    )

    with pytest.raises(RobotLoadError) as e:
        await device.set(sample_location)
        assert e.value.error_code == 40

    expected_load_unload_calls = (
        [call.reset.put(None), call.unload.put(None)]
        if sample_location is SAMPLE_LOCATION_EMPTY
        else [
            call.reset.put(None),
            call.next_puck.put(ANY),
            call.next_pin.put(ANY),
            call.load.put(None),
        ]
    )
    get_mock(device).assert_has_calls(expected_load_unload_calls)


async def test_robot_load_resets_controller_error_and_succeeds_if_error_cleared(
    robot_for_load: BartRobot,
):
    device = robot_for_load
    _set_fast_robot_timeouts(device)
    set_mock_value(
        device.controller_error.code, ControllerErrorCode.LIGHT_CURTAIN_TRIPPED.value
    )

    await device.set(SampleLocation(15, 10))

    get_mock(device).assert_has_calls(
        [
            call.reset.put(None),
            call.next_puck.put(ANY),
            call.next_pin.put(ANY),
            call.load.put(None),
        ]
    )


async def test_robot_load_resets_prog_error_and_succeeds_if_error_cleared(
    robot_for_load: BartRobot,
):
    device = robot_for_load
    _set_fast_robot_timeouts(device)
    set_mock_value(
        device.prog_error.code, ProgErrorCode.SAMPLE_POSITION_NOT_READY.value
    )

    await device.set(SampleLocation(15, 10))

    get_mock(device).assert_has_calls(
        [
            call.reset.put(None),
            call.next_puck.put(ANY),
            call.next_pin.put(ANY),
            call.load.put(None),
        ]
    )


async def test_robot_unload_resets_controller_error_and_succeeds_if_error_cleared(
    robot_for_unload,
):
    device, trigger_complete, drying_complete = robot_for_unload
    trigger_complete.set()
    drying_complete.set()
    set_mock_value(
        device.controller_error.code, ControllerErrorCode.LIGHT_CURTAIN_TRIPPED.value
    )

    await device.set(SAMPLE_LOCATION_EMPTY)

    get_mock(device).assert_has_calls([call.reset.put(None), call.unload.put(None)])


async def test_robot_unload_resets_prog_error_and_succeeds_if_error_cleared(
    robot_for_unload,
):
    device, trigger_complete, drying_complete = robot_for_unload
    trigger_complete.set()
    drying_complete.set()
    set_mock_value(
        device.prog_error.code, ProgErrorCode.SAMPLE_POSITION_NOT_READY.value
    )

    await device.set(SAMPLE_LOCATION_EMPTY)

    get_mock(device).assert_has_calls([call.reset.put(None), call.unload.put(None)])


async def test_robot_load_does_not_reset_if_prog_error_or_controller_error_not_retryable(
    robot_for_load,
):
    robot = robot_for_load
    set_mock_value(robot.prog_error.code, 123)
    set_mock_value(
        robot.controller_error.code, ControllerErrorCode.LIGHT_CURTAIN_TRIPPED.value
    )

    with pytest.raises(RobotLoadError) as e:
        await robot.set(SampleLocation(1, 2))

    get_mock_put(robot.reset).assert_not_called()
    assert e.value.error_code == 123

    set_mock_value(robot.prog_error.code, ProgErrorCode.SAMPLE_POSITION_NOT_READY)
    set_mock_value(robot.controller_error.code, 123)

    with pytest.raises(RobotLoadError):
        await robot.set(SampleLocation(1, 2))

    get_mock_put(robot.reset).assert_not_called()
    assert e.value.error_code == 123


async def test_unloading_the_robot_waits_for_drying_to_complete(robot_for_unload):
    robot, trigger_completed, drying_completed = robot_for_unload
    drying_completed.set()
    unload_status = robot.set(SAMPLE_LOCATION_EMPTY)

    await asyncio.sleep(0.1)
    assert not unload_status.done
    get_mock_put(robot.unload).assert_called_once()

    trigger_completed.set()
    await unload_status
    assert unload_status.done


async def test_unloading_the_robot_times_out_if_unloading_takes_too_long(
    robot_for_unload,
):
    robot, trigger_completed, drying_completed = robot_for_unload
    drying_completed.set()
    unload_status = robot.set(SAMPLE_LOCATION_EMPTY)

    with pytest.raises(RobotLoadError) as exc_info:
        await unload_status

    assert isinstance(exc_info.value.__cause__, TimeoutError)


async def test_unloading_the_robot_times_out_if_drying_takes_too_long(robot_for_unload):
    robot, trigger_completed, drying_completed = robot_for_unload
    trigger_completed.set()
    unload_status = robot.set(SAMPLE_LOCATION_EMPTY)

    with pytest.raises(RobotLoadError) as exc_info:
        await unload_status

    assert isinstance(exc_info.value.__cause__, TimeoutError)


async def test_moving_the_robot_will_raise_if_prog_error_during_unload(
    robot_for_load_with_prog_error: BartRobot,
):
    device = robot_for_load_with_prog_error

    with pytest.raises(RobotLoadError) as exc_info:
        await device.set(SampleLocation(15, 10))

    assert exc_info.value.error_code == ProgErrorCode.SAMPLE_POSITION_NOT_READY
    assert exc_info.value.error_string == "Test error"


async def test_moving_the_robot_will_raise_if_controller_error_during_unload(
    robot_for_load_with_controller_error: BartRobot,
):
    device = robot_for_load_with_controller_error

    with pytest.raises(RobotLoadError) as exc_info:
        await device.set(SampleLocation(15, 10))

    assert exc_info.value.error_code == ControllerErrorCode.LIGHT_CURTAIN_TRIPPED
    assert exc_info.value.error_string == "Test error"
