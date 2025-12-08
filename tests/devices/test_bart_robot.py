import asyncio
import traceback
from asyncio import Event, create_task
from functools import partial
from unittest.mock import ANY, AsyncMock, MagicMock, call, patch

import pytest
from ophyd_async.core import (
    AsyncStatus,
    callback_on_mock_put,
    get_mock,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.robot import (
    WAIT_FOR_NEW_PIN_MSG,
    WAIT_FOR_OLD_PIN_MSG,
    BartRobot,
    PinMounted,
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
        set_mock_value(device.program_running, False)

    async def fake_unload(*args, **kwargs):
        set_mock_value(device.program_running, True)
        await trigger_complete.wait()
        asyncio.create_task(finish_later())

    get_mock_put(device.unload).side_effect = fake_unload
    return device, trigger_complete, drying_complete


async def _get_bart_robot() -> BartRobot:
    device = BartRobot("robot", "-MO-ROBOT-01:")
    device.LOAD_TIMEOUT = 1  # type: ignore
    device.NOT_BUSY_TIMEOUT = 1  # type: ignore
    await device.connect(mock=True)
    return device


# For tests which are intentionally triggering a timeout error
def _set_fast_robot_timeouts(robot: BartRobot):
    robot.LOAD_TIMEOUT = 0.01  # type: ignore
    robot.NOT_BUSY_TIMEOUT = 0.01  # type: ignore


async def test_bart_robot_can_be_connected_in_sim_mode():
    device = await _get_bart_robot()
    await device.connect(mock=True)


async def test_given_robot_load_times_out_when_load_called_then_exception_contains_error_info():
    device = await _get_bart_robot()
    _set_fast_robot_timeouts(device)
    device._load_pin_and_puck = AsyncMock(side_effect=TimeoutError)

    set_mock_value(device.prog_error.code, (expected_error_code := 10))
    set_mock_value(device.prog_error.str, (expected_error_string := "BAD"))

    with pytest.raises(RobotLoadError) as e:
        await device.set(SampleLocation(0, 0))
    assert e.value.error_code == expected_error_code
    assert e.value.error_string == expected_error_string
    assert str(e.value) == expected_error_string


@patch("dodal.devices.robot.LOGGER")
async def test_given_program_running_when_load_pin_then_logs_the_program_name_and_times_out(
    patch_logger: MagicMock,
):
    device = await _get_bart_robot()
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
    patch_logger: MagicMock,
):
    device = await _get_bart_robot()
    _set_fast_robot_timeouts(device)
    set_mock_value(device.program_running, False)
    set_mock_value(device.gonio_pin_sensor, PinMounted.PIN_MOUNTED)
    device.load = AsyncMock(side_effect=device.load)
    with pytest.raises(RobotLoadError):
        await device.set(SampleLocation(15, 10))
    device.load.trigger.assert_called_once()  # type:ignore
    last_log = patch_logger.mock_calls[1].args[0]
    assert "Waiting on old pin unloaded" in last_log


@patch("dodal.devices.robot.LOGGER")
async def test_given_program_not_running_and_pin_unmounting_but_new_pin_not_mounting_when_load_pin_then_timeout(
    patch_logger: MagicMock,
):
    device = await _get_bart_robot()
    _set_fast_robot_timeouts(device)
    set_mock_value(device.program_running, False)
    set_mock_value(device.gonio_pin_sensor, PinMounted.NO_PIN_MOUNTED)
    device.load = AsyncMock(side_effect=device.load)
    with pytest.raises(RobotLoadError) as exc_info:
        await device.set(SampleLocation(15, 10))

    try:
        device.load.trigger.assert_called_once()  # type:ignore
        last_log = patch_logger.mock_calls[1].args[0]
        assert "Waiting on new pin loaded" in last_log
    except AssertionError:
        traceback.print_exception(exc_info.value)
        raise


def _set_pin_sensor_on_log_messages(device: BartRobot, msg: str):
    if msg == WAIT_FOR_OLD_PIN_MSG:
        set_mock_value(device.gonio_pin_sensor, PinMounted.NO_PIN_MOUNTED)
    elif msg == WAIT_FOR_NEW_PIN_MSG:
        set_mock_value(device.gonio_pin_sensor, PinMounted.PIN_MOUNTED)


def _error_on_unload_log_messages(device: BartRobot, msg: str):
    if msg == WAIT_FOR_OLD_PIN_MSG:
        set_mock_value(device.prog_error.code, 40)
        set_mock_value(device.prog_error.str, "Test error")


# Use log info messages to determine when to set the gonio_pin_sensor, so we don't have to use any sleeps during testing
async def set_with_happy_path(
    device: BartRobot, mock_log_info: MagicMock
) -> AsyncStatus:
    """Mocks the logic that the robot would do on a successful load"""

    mock_log_info.side_effect = partial(_set_pin_sensor_on_log_messages, device)
    set_mock_value(device.program_running, False)
    set_mock_value(device.gonio_pin_sensor, PinMounted.PIN_MOUNTED)
    status = device.set(SampleLocation(15, 10))
    return status


async def set_with_unhappy_path(
    device: BartRobot, mock_log_info: MagicMock
) -> AsyncStatus:
    """Mocks the logic that the robot would do on a successful load"""

    mock_log_info.side_effect = partial(_error_on_unload_log_messages, device)
    set_mock_value(device.program_running, False)
    set_mock_value(device.gonio_pin_sensor, PinMounted.PIN_MOUNTED)
    status = device.set(SampleLocation(15, 10))
    return status


@patch("dodal.devices.robot.LOGGER.info")
async def test_given_program_not_running_and_pin_unmounts_then_mounts_when_load_pin_then_pin_loaded(
    mock_log_info: MagicMock,
):
    device = await _get_bart_robot()
    status = await set_with_happy_path(device, mock_log_info)
    await status
    assert status.success
    assert (await device.next_puck.get_value()) == 15
    assert (await device.next_pin.get_value()) == 10
    get_mock_put(device.load).assert_called_once()


async def test_given_waiting_for_pin_to_mount_when_no_pin_mounted_then_error_raised():
    device = await _get_bart_robot()
    set_mock_value(device.prog_error.code, 25)
    status = device.pin_state_or_error()
    with pytest.raises(RobotLoadError):
        await status


async def test_given_waiting_for_pin_to_mount_when_pin_mounted_then_no_error_raised():
    device = await _get_bart_robot()
    status = create_task(device.pin_state_or_error())
    set_mock_value(device.gonio_pin_sensor, PinMounted.PIN_MOUNTED)
    await status


@patch("dodal.devices.robot.wait_for")
async def test_set_waits_for_both_timeouts(mock_wait_for: AsyncMock):
    device = await _get_bart_robot()
    _set_fast_robot_timeouts(device)
    device._load_pin_and_puck = MagicMock()  # type: ignore
    await device.set(SampleLocation(1, 2))
    mock_wait_for.assert_awaited_once_with(ANY, timeout=0.02)


async def test_moving_the_robot_will_reset_error_if_light_curtain_is_tripped_and_still_throw_if_error_not_cleared():
    device = await _get_bart_robot()
    _set_fast_robot_timeouts(device)
    set_mock_value(device.controller_error.code, BartRobot.LIGHT_CURTAIN_TRIPPED)

    with pytest.raises(RobotLoadError) as e:
        await device.set(SampleLocation(1, 2))
        assert e.value.error_code == 40

    get_mock(device).assert_has_calls(
        [
            call.reset.put(None, wait=True),
            call.next_puck.put(ANY, wait=True),
            call.next_pin.put(ANY, wait=True),
            call.load.put(None, wait=True),
        ]
    )


@patch("dodal.devices.robot.LOGGER.info")
async def test_moving_the_robot_will_reset_error_if_light_curtain_is_tripped_and_continue_if_error_cleared(
    mock_log_info: MagicMock,
):
    device = await _get_bart_robot()
    set_mock_value(device.controller_error.code, BartRobot.LIGHT_CURTAIN_TRIPPED)

    callback_on_mock_put(
        device.reset,
        lambda *_, **__: set_mock_value(device.controller_error.code, 0),
    )

    await (await set_with_happy_path(device, mock_log_info))

    get_mock(device).assert_has_calls(
        [
            call.reset.put(None, wait=True),
            call.next_puck.put(ANY, wait=True),
            call.next_pin.put(ANY, wait=True),
            call.load.put(None, wait=True),
        ]
    )


async def test_unloading_the_robot_waits_for_drying_to_complete(robot_for_unload):
    robot, trigger_completed, drying_completed = robot_for_unload
    drying_completed.set()
    unload_status = robot.set(None)

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
    unload_status = robot.set(None)

    with pytest.raises(RobotLoadError) as exc_info:
        await unload_status

    assert isinstance(exc_info.value.__cause__, TimeoutError)


async def test_unloading_the_robot_times_out_if_drying_takes_too_long(robot_for_unload):
    robot, trigger_completed, drying_completed = robot_for_unload
    trigger_completed.set()
    unload_status = robot.set(None)

    with pytest.raises(RobotLoadError) as exc_info:
        await unload_status

    assert isinstance(exc_info.value.__cause__, TimeoutError)


@patch("dodal.devices.robot.LOGGER.info")
async def test_moving_the_robot_will_raise_if_error_during_unload(
    mock_log_info: MagicMock,
):
    device = await _get_bart_robot()

    with pytest.raises(RobotLoadError) as exc_info:
        await (await set_with_unhappy_path(device, mock_log_info))

    assert exc_info.value.error_code == 40
    assert exc_info.value.error_string == "Test error"
