from unittest.mock import ANY, call

import pytest
from ophyd_async.core import (
    callback_on_mock_put,
    get_mock,
    get_mock_put,
    init_devices,
    set_mock_value,
)

from dodal.devices.beamlines.i15_1.robot import ProgramRunning, Robot, SampleLocation


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


async def test_puck_program_loaded_before_position_selected(robot: Robot) -> None:
    set_location = SampleLocation(location=1, pin=2)
    await robot.set(set_location)

    parent_mock = get_mock(robot)

    assert parent_mock.mock_calls[0] == call.puck_load_program.put(ANY, wait=True)
    assert parent_mock.mock_calls[1] == call.puck_sel.put(ANY, wait=True)
    assert parent_mock.mock_calls[2] == call.pos_sel.put(ANY, wait=True)

    get_mock_put(robot.puck_sel).assert_called_once_with(1, wait=True)
    get_mock_put(robot.pos_sel).assert_called_once_with(2, wait=True)


async def test_given_wrong_program_gets_loaded_robot_times_out(robot: Robot):
    def change_to_wrong_program(*_, **__):
        set_mock_value(robot.program_name, "BAD PROGRAM")

    callback_on_mock_put(robot.puck_load_program, change_to_wrong_program)

    robot.PROGRAM_LOADED_TIMEOUT = 0.01

    with pytest.raises(TimeoutError):
        await robot.set(SampleLocation(location=1, pin=2))

    get_mock_put(robot.puck_pick).assert_not_called()


async def test_given_program_doesnt_start_then_robot_timesout(robot: Robot):
    def do_nothing(*_, **__):
        pass

    callback_on_mock_put(robot.puck_pick, do_nothing)

    robot.PROGRAM_STARTED_RUNNING_TIMEOUT = 0.01

    with pytest.raises(TimeoutError):
        await robot.set(SampleLocation(location=1, pin=2))


async def test_given_program_doesnt_stop_then_robot_timesout(robot: Robot):
    def do_nothing(*_, **__):
        set_mock_value(robot.program_running, ProgramRunning.PROGRAM_RUNNING)

    callback_on_mock_put(robot.puck_pick, do_nothing)

    robot.PROGRAM_COMPLETED_TIMEOUT = 0.01

    with pytest.raises(TimeoutError):
        await robot.set(SampleLocation(location=1, pin=2))
