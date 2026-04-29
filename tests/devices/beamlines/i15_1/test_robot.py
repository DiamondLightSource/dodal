from unittest.mock import ANY, call

import pytest
from ophyd_async.core import (
    callback_on_mock_put,
    get_mock,
    get_mock_put,
    init_devices,
    set_mock_value,
)

from dodal.devices.beamlines.i15_1.robot import (
    SAMPLE_LOCATION_EMPTY,
    ProgramRunning,
    Robot,
    SampleLocation,
    SpinnerState,
)


@pytest.fixture
async def robot() -> Robot:
    async with init_devices(mock=True):
        robot = Robot(robot_prefix="", current_sample_prefix="")

    set_mock_value(robot.puck_sel, 0)  # Set initial position
    set_mock_value(robot.pos_sel, 0)  # Set initial position

    robot.PROGRAM_LOADED_TIMEOUT = 0.05
    robot.PROGRAM_STARTED_RUNNING_TIMEOUT = 0.05
    robot.PROGRAM_COMPLETED_TIMEOUT = 0.05

    return robot


async def test_set_moves_to_position(robot: Robot) -> None:
    set_location = SampleLocation(puck=1, position=2)
    await robot.set(set_location)

    assert await robot.puck_sel.get_value() == 1
    assert await robot.pos_sel.get_value() == 2


async def test_puck_program_loaded_before_position_selected(robot: Robot) -> None:
    set_location = SampleLocation(puck=1, position=2)
    await robot.set(set_location)

    parent_mock = get_mock(robot)

    expected_calls = [
        call.puck_load_program.put(ANY),
        call.puck_sel.put(ANY),
        call.pos_sel.put(ANY),
    ]

    parent_mock.assert_has_calls(expected_calls, any_order=False)

    get_mock_put(robot.puck_sel).assert_called_once_with(1)
    get_mock_put(robot.pos_sel).assert_called_once_with(2)


async def test_given_wrong_puck_program_gets_loaded_robot_times_out(robot: Robot):
    def change_to_wrong_program(*_, **__):
        set_mock_value(robot.program_name, "BAD PROGRAM")

    callback_on_mock_put(robot.puck_load_program, change_to_wrong_program)

    with pytest.raises(TimeoutError):
        await robot.set(SampleLocation(puck=1, position=2))

    get_mock_put(robot.puck_pick).assert_not_called()


async def test_given_puck_program_doesnt_start_then_robot_times_out(robot: Robot):
    def do_nothing(*_, **__):
        pass

    callback_on_mock_put(robot.puck_pick, do_nothing)

    with pytest.raises(TimeoutError):
        await robot.set(SampleLocation(puck=1, position=2))


async def test_given_puck_program_doesnt_stop_then_robot_times_out(robot: Robot):
    def infinite_program(*_, **__):
        set_mock_value(robot.program_running, ProgramRunning.PROGRAM_RUNNING)

    callback_on_mock_put(robot.puck_pick, infinite_program)

    with pytest.raises(TimeoutError):
        await robot.set(SampleLocation(puck=1, position=2))


async def test_when_robot_loaded_puck_picked_then_beam_placed(robot: Robot) -> None:
    set_location = SampleLocation(puck=1, position=2)
    await robot.set(set_location)

    parent_mock = get_mock(robot)

    calls = parent_mock.mock_calls

    puck_program_loaded = calls.index(call.puck_load_program.put(ANY))
    puck_picked = calls.index(call.puck_pick.put(ANY))

    beam_program_loaded = calls.index(call.beam_load_program.put(ANY))
    beam_placed = calls.index(call.beam_place.put(ANY))

    assert puck_program_loaded < puck_picked < beam_program_loaded < beam_placed


async def test_given_wrong_beam_program_gets_loaded_robot_times_out(robot: Robot):
    def change_to_wrong_program(*_, **__):
        set_mock_value(robot.program_name, "BAD PROGRAM")

    callback_on_mock_put(robot.beam_load_program, change_to_wrong_program)

    with pytest.raises(TimeoutError):
        await robot.set(SampleLocation(puck=1, position=2))

    get_mock_put(robot.beam_place).assert_not_called()


async def test_given_beam_program_doesnt_start_then_robot_times_out(robot: Robot):
    def do_nothing(*_, **__):
        pass

    callback_on_mock_put(robot.beam_place, do_nothing)

    with pytest.raises(TimeoutError):
        await robot.set(SampleLocation(puck=1, position=2))


async def test_given_beam_program_doesnt_stop_then_robot_times_out(robot: Robot):
    def infinite_program(*_, **__):
        set_mock_value(robot.program_running, ProgramRunning.PROGRAM_RUNNING)

    callback_on_mock_put(robot.beam_place, infinite_program)

    with pytest.raises(TimeoutError):
        await robot.set(SampleLocation(puck=1, position=2))


async def test_after_robot_load_new_sample_position_is_put_in_index_pvs(robot: Robot):
    await robot.set(SampleLocation(puck=1, position=2))

    assert await robot.current_sample.puck.get_value() == 1
    assert await robot.current_sample.position.get_value() == 2


async def test_given_loaded_from_a_position_then_unload_moves_to_position(
    robot: Robot,
) -> None:
    set_mock_value(robot.current_sample.puck, 1)
    set_mock_value(robot.current_sample.position, 2)

    await robot.set(SAMPLE_LOCATION_EMPTY)

    assert await robot.puck_sel.get_value() == 1
    assert await robot.pos_sel.get_value() == 2


async def test_given_spinner_started_then_can_read_spinner_state(
    robot: Robot,
):
    await robot.spinner.set(SpinnerState.ON)

    assert await robot.spinner.get_value() == SpinnerState.ON


async def test_when_unloaded_then_spinner_stops_before_beam_program_loaded(
    robot: Robot,
) -> None:
    set_mock_value(robot.current_sample.puck, 1)
    set_mock_value(robot.current_sample.position, 2)

    await robot.set(SAMPLE_LOCATION_EMPTY)

    parent_mock = get_mock(robot)

    expected_calls = [
        call._spinner_load_program.put(ANY),
        call._spinner_off.put(ANY),
        call.beam_load_program.put(ANY),
    ]

    parent_mock.assert_has_calls(expected_calls, any_order=False)


async def test_given_wrong_spinner_program_gets_loaded_then_times_out(robot: Robot):
    def change_to_wrong_program(*_, **__):
        set_mock_value(robot.program_name, "BAD PROGRAM")

    callback_on_mock_put(robot._spinner_load_program, change_to_wrong_program)

    with pytest.raises(TimeoutError):
        await robot.spinner.set(SpinnerState.OFF)

    get_mock_put(robot._spinner_off).assert_not_called()


async def test_given_spinner_stop_program_doesnt_start_then_times_out(
    robot: Robot,
):
    def do_nothing(*_, **__):
        pass

    callback_on_mock_put(robot._spinner_off, do_nothing)

    with pytest.raises(TimeoutError):
        await robot.spinner.set(SpinnerState.OFF)


async def test_given_spinner_stop_program_doesnt_stop_then_times_out(
    robot: Robot,
):
    def infinite_program(*_, **__):
        set_mock_value(robot.program_running, ProgramRunning.PROGRAM_RUNNING)

    callback_on_mock_put(robot._spinner_off, infinite_program)

    with pytest.raises(TimeoutError):
        await robot.spinner.set(SpinnerState.OFF)


@pytest.mark.parametrize(
    "initial_state",
    (SpinnerState.ON, SpinnerState.OFF),
)
async def test_given_spinner_is_already_in_state_then_dont_change_it(
    robot: Robot,
    initial_state: SpinnerState,
):
    set_mock_value(robot._spinner_rbv, initial_state)

    await robot.spinner.set(initial_state)

    get_mock_put(robot._spinner_load_program).assert_not_called()


async def test_when_robot_unloaded_beam_picked_then_puck_placed(robot: Robot) -> None:
    set_mock_value(robot.current_sample.puck, 1)
    set_mock_value(robot.current_sample.position, 2)

    await robot.set(SAMPLE_LOCATION_EMPTY)

    parent_mock = get_mock(robot)

    calls = parent_mock.mock_calls

    beam_program_loaded = calls.index(call.beam_load_program.put(ANY))
    beam_picked = calls.index(call.beam_pick.put(ANY))

    puck_program_loaded = calls.index(call.puck_load_program.put(ANY))
    puck_placed = calls.index(call.puck_place.put(ANY))

    assert beam_program_loaded < beam_picked < puck_program_loaded < puck_placed


async def test_after_robot_unload_new_0_0_is_put_in_index_pvs(robot: Robot):
    await robot.set(SAMPLE_LOCATION_EMPTY)

    assert await robot.current_sample.puck.get_value() == 0
    assert await robot.current_sample.position.get_value() == 0
