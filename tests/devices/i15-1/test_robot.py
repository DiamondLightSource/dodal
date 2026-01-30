from unittest.mock import ANY, call

import pytest
from ophyd_async.core import (
    callback_on_mock_put,
    get_mock,
    get_mock_put,
    init_devices,
    set_mock_value,
)

from dodal.devices.i15_1.robot import Robot, SampleLocation


@pytest.fixture
async def robot() -> Robot:
    async with init_devices(mock=True):
        robot = Robot(prefix="")

    set_mock_value(robot.puck_sel, 0)  # Set initial position
    set_mock_value(robot.pos_sel, 0)  # Set initial position

    return robot


async def test_set_moves_to_position(robot: Robot) -> None:
    set_location = SampleLocation(location=1, pin=2)
    await robot.set(set_location)

    assert await robot.puck_sel.get_value() == 1
    assert await robot.pos_sel.get_value() == 2
    # assert await robot.program_name.get_value() == "PUCK.MB6"


async def test_puck_program_loaded_before_position_selected(robot: Robot) -> None:
    set_location = SampleLocation(location=1, pin=2)
    await robot.set(set_location)

    parent_mock = get_mock(robot)

    assert parent_mock.mock_calls[0] == call.puck_load_program.put(ANY, wait=True)
    assert parent_mock.mock_calls[1] == call.puck_sel.put(ANY, wait=True)
    assert parent_mock.mock_calls[2] == call.pos_sel.put(ANY, wait=True)

    get_mock_put(robot.puck_sel).assert_called_once_with(1, wait=True)
    get_mock_put(robot.pos_sel).assert_called_once_with(2, wait=True)

    # located_position = await robot.locate()
    # assert located_position["setpoint"] == set_location


async def test_trigger_causes_running_logic(robot: Robot):
    set_location = SampleLocation(location=1, pin=2)
    await robot.set(set_location)


async def test_given_wrong_program_gets_loaded_robot_timesout(robot: Robot):
    def change_program_name(*args, **kwargs):
        set_mock_value(robot.program_name, "BAD PROGRAM")

    callback_on_mock_put(robot.puck_load_program, change_program_name)

    robot.PROGRAM_LOADED_TIMEOUT = 0.01

    set_location = SampleLocation(location=1, pin=2)
    with pytest.raises(TimeoutError):
        await robot.set(set_location)
