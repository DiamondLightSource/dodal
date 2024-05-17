from asyncio import TimeoutError, sleep
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ophyd_async.core import set_mock_value

from dodal.devices.robot import BartRobot, PinMounted, SampleLocation


async def _get_bart_robot() -> BartRobot:
    device = BartRobot("robot", "-MO-ROBOT-01:")
    device.LOAD_TIMEOUT = 0.01  # type: ignore
    await device.connect(mock=True)
    return device


async def test_bart_robot_can_be_connected_in_sim_mode():
    device = await _get_bart_robot()
    await device.connect(mock=True)


@patch("dodal.devices.robot.LOGGER")
async def test_given_program_running_when_load_pin_then_logs_the_program_name_and_times_out(
    patch_logger: MagicMock,
):
    device = await _get_bart_robot()
    program_name = "BAD_PROGRAM"
    set_mock_value(device.program_running, True)
    set_mock_value(device.program_name, program_name)
    with pytest.raises(TimeoutError):
        await device.set(SampleLocation(0, 0))
    last_log = patch_logger.mock_calls[1].args[0]
    assert program_name in last_log


@patch("dodal.devices.robot.LOGGER")
async def test_given_program_not_running_but_pin_not_unmounting_when_load_pin_then_timeout(
    patch_logger: MagicMock,
):
    device = await _get_bart_robot()
    set_mock_value(device.program_running, False)
    set_mock_value(device.gonio_pin_sensor, PinMounted.PIN_MOUNTED)
    device.load = AsyncMock(side_effect=device.load)
    with pytest.raises(TimeoutError):
        await device.set(SampleLocation(15, 10))
    device.load.trigger.assert_called_once()  # type:ignore
    last_log = patch_logger.mock_calls[1].args[0]
    assert "Waiting on old pin unloaded" in last_log


@patch("dodal.devices.robot.LOGGER")
async def test_given_program_not_running_and_pin_unmounting_but_new_pin_not_mounting_when_load_pin_then_timeout(
    patch_logger: MagicMock,
):
    device = await _get_bart_robot()
    set_mock_value(device.program_running, False)
    set_mock_value(device.gonio_pin_sensor, PinMounted.NO_PIN_MOUNTED)
    device.load = AsyncMock(side_effect=device.load)
    with pytest.raises(TimeoutError):
        await device.set(SampleLocation(15, 10))
    device.load.trigger.assert_called_once()  # type:ignore
    last_log = patch_logger.mock_calls[1].args[0]
    assert "Waiting on new pin loaded" in last_log


async def test_given_program_not_running_and_pin_unmounts_then_mounts_when_load_pin_then_pin_loaded():
    device = await _get_bart_robot()
    device.LOAD_TIMEOUT = 0.03  # type: ignore
    set_mock_value(device.program_running, False)
    set_mock_value(device.gonio_pin_sensor, PinMounted.PIN_MOUNTED)

    device.load = AsyncMock(side_effect=device.load)
    status = device.set(SampleLocation(15, 10))
    await sleep(0.01)
    set_mock_value(device.gonio_pin_sensor, PinMounted.NO_PIN_MOUNTED)
    await sleep(0.005)
    set_mock_value(device.gonio_pin_sensor, PinMounted.PIN_MOUNTED)
    await status
    assert status.success
    assert (await device.next_puck.get_value()) == 15
    assert (await device.next_pin.get_value()) == 10
    device.load.trigger.assert_called_once()  # type:ignore
