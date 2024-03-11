from asyncio import TimeoutError
from unittest.mock import AsyncMock

import pytest
from ophyd_async.core import set_sim_value

from dodal.devices.robot import BartRobot, SampleLocation


async def _get_bart_robot() -> BartRobot:
    device = BartRobot("robot", "-MO-ROBOT-01:")
    device.LOAD_TIMEOUT = 0.01  # type: ignore
    await device.connect(sim=True)
    return device


@pytest.mark.asyncio
async def test_bart_robot_can_be_connected_in_sim_mode():
    device = await _get_bart_robot()
    await device.connect(sim=True)


@pytest.mark.asyncio
async def test_when_barcode_updates_then_new_barcode_read():
    device = await _get_bart_robot()
    expected_barcode = "expected"
    set_sim_value(device.barcode.bare_signal, [expected_barcode, "other_barcode"])
    assert (await device.barcode.read())["robot-barcode"]["value"] == expected_barcode


@pytest.mark.asyncio
async def test_given_program_running_when_load_pin_then_times_out():
    device = await _get_bart_robot()
    set_sim_value(device.program_running, True)
    with pytest.raises(TimeoutError):
        await device.set(SampleLocation(0, 0))


@pytest.mark.asyncio
async def test_given_program_not_running_when_load_pin_then_pin_loaded():
    device = await _get_bart_robot()
    set_sim_value(device.program_running, False)
    set_sim_value(device.gonio_pin_sensor, True)
    device.load = AsyncMock(side_effect=device.load)
    status = device.set(SampleLocation(15, 10))
    await status
    assert status.success
    assert (await device.next_puck.get_value()) == 15
    assert (await device.next_pin.get_value()) == 10
    device.load.trigger.assert_called_once()  # type:ignore


@pytest.mark.asyncio
async def test_given_program_not_running_but_pin_not_mounting_when_load_pin_then_timeout():
    device = await _get_bart_robot()
    set_sim_value(device.program_running, False)
    set_sim_value(device.gonio_pin_sensor, False)
    device.load = AsyncMock(side_effect=device.load)
    with pytest.raises(TimeoutError):
        await device.set(SampleLocation(15, 10))
    device.load.trigger.assert_called_once()  # type:ignore
