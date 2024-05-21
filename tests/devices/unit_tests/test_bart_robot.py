from asyncio import TimeoutError, sleep
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ophyd_async.core import set_mock_value

from dodal.devices.robot import PinMounted, SampleLocation


async def test_bart_robot_can_be_connected_in_sim_mode(mock_bart_robot):
    await mock_bart_robot.connect(mock=True)


@patch("dodal.devices.robot.LOGGER")
async def test_given_program_running_when_load_pin_then_logs_the_program_name_and_times_out(
    patch_logger: MagicMock,
    mock_bart_robot,
):
    program_name = "BAD_PROGRAM"
    set_mock_value(mock_bart_robot.program_running, True)
    set_mock_value(mock_bart_robot.program_name, program_name)
    with pytest.raises(TimeoutError):
        await mock_bart_robot.set(SampleLocation(0, 0))
    last_log = patch_logger.mock_calls[1].args[0]
    assert program_name in last_log


@patch("dodal.devices.robot.LOGGER")
async def test_given_program_not_running_but_pin_not_unmounting_when_load_pin_then_timeout(
    patch_logger: MagicMock,
    mock_bart_robot,
):
    set_mock_value(mock_bart_robot.program_running, False)
    set_mock_value(mock_bart_robot.gonio_pin_sensor, PinMounted.PIN_MOUNTED)
    mock_bart_robot.load = AsyncMock(side_effect=mock_bart_robot.load)
    with pytest.raises(TimeoutError):
        await mock_bart_robot.set(SampleLocation(15, 10))
    mock_bart_robot.load.trigger.assert_called_once()  # type:ignore
    last_log = patch_logger.mock_calls[1].args[0]
    assert "Waiting on old pin unloaded" in last_log


@patch("dodal.devices.robot.LOGGER")
async def test_given_program_not_running_and_pin_unmounting_but_new_pin_not_mounting_when_load_pin_then_timeout(
    patch_logger: MagicMock,
    mock_bart_robot,
):
    set_mock_value(mock_bart_robot.program_running, False)
    set_mock_value(mock_bart_robot.gonio_pin_sensor, PinMounted.NO_PIN_MOUNTED)
    mock_bart_robot.load = AsyncMock(side_effect=mock_bart_robot.load)
    with pytest.raises(TimeoutError):
        await mock_bart_robot.set(SampleLocation(15, 10))
    mock_bart_robot.load.trigger.assert_called_once()  # type:ignore
    last_log = patch_logger.mock_calls[1].args[0]
    assert "Waiting on new pin loaded" in last_log


async def test_given_program_not_running_and_pin_unmounts_then_mounts_when_load_pin_then_pin_loaded(
    mock_bart_robot,
):
    mock_bart_robot.LOAD_TIMEOUT = 0.03  # type: ignore
    set_mock_value(mock_bart_robot.program_running, False)
    set_mock_value(mock_bart_robot.gonio_pin_sensor, PinMounted.PIN_MOUNTED)

    mock_bart_robot.load = AsyncMock(side_effect=mock_bart_robot.load)
    status = mock_bart_robot.set(SampleLocation(15, 10))
    await sleep(0.01)
    set_mock_value(mock_bart_robot.gonio_pin_sensor, PinMounted.NO_PIN_MOUNTED)
    await sleep(0.005)
    set_mock_value(mock_bart_robot.gonio_pin_sensor, PinMounted.PIN_MOUNTED)
    await status
    assert status.success
    assert (await mock_bart_robot.next_puck.get_value()) == 15
    assert (await mock_bart_robot.next_pin.get_value()) == 10
    mock_bart_robot.load.trigger.assert_called_once()  # type:ignore
