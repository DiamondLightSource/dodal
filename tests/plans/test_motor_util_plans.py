from typing import Dict, List
from unittest.mock import ANY, call

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd_async.core import Device, DeviceCollector, get_mock_put, set_mock_value
from ophyd_async.core.signal import Signal, soft_signal_rw
from ophyd_async.epics.motion import Motor

from dodal.devices.util.test_utils import patch_motor
from dodal.plans.motor_util_plans import (
    MoveTooLarge,
    _check_and_cache_values,
    home_and_reset_wrapper,
)


class TestMotorDevice(Device):
    motors: List[Motor]
    not_motors: List[Signal]


class DeviceWithOnlyMotors(TestMotorDevice):
    def __init__(self):
        self.x = Motor("X")
        self.y = Motor("Y")
        self.motors = [self.x, self.y]
        self.not_motors = []
        super().__init__("")


class DeviceWithNoMotors(Device):
    def __init__(self):
        self.x = soft_signal_rw(float, 100)
        self.y = soft_signal_rw(float, 200)
        self.motors = []
        self.not_motors = [self.x, self.y]
        super().__init__("")


class DeviceWithSomeMotors(Device):
    def __init__(self):
        self.x = soft_signal_rw(float, 100)
        self.y = Motor("Y")
        self.motors = [self.y]
        self.not_motors = [self.x]
        super().__init__("")


@pytest.fixture
def my_device(RE):
    with DeviceCollector(mock=True):
        my_device = DeviceWithOnlyMotors()
    return my_device


@pytest.mark.parametrize(
    "device",
    [
        DeviceWithOnlyMotors,
        DeviceWithNoMotors,
        DeviceWithSomeMotors,
    ],
)
def test_given_a_device_when_check_and_cache_values_then_motor_values_returned(device):
    RE = RunEngine(call_returns_result=True)
    with DeviceCollector(mock=True):
        my_device: TestMotorDevice = device()

    for i, motor in enumerate(my_device.motors, start=1):
        set_mock_value(motor.user_readback, i * 100)

    motors_and_positions: Dict[Motor, float] = RE(
        _check_and_cache_values(my_device, 0, 1000)
    ).plan_result  # type: ignore
    cached_positions = motors_and_positions.values()

    assert len(cached_positions) == len(my_device.motors)
    for i, cached_position in enumerate(cached_positions, start=1):
        assert cached_position, i * 100


@pytest.mark.parametrize(
    "initial, max, home",
    [
        (200, 100, 0),
        (-200, 100, 0),
        (-200, 100, -50),
        (-200, 100, 50),
    ],
)
def test_given_a_device_with_a_too_large_move_when_check_and_cache_values_then_exception_thrown(
    RE, my_device, initial, max, home
):
    set_mock_value(my_device.x.user_readback, 10)
    set_mock_value(my_device.y.user_readback, initial)

    with pytest.raises(MoveTooLarge) as e:
        RE(_check_and_cache_values(my_device, 0, max, home_position=home))
        assert e.value.axis == my_device.y
        assert e.value.maximum_move == max


@pytest.mark.parametrize(
    "initial, min, home",
    [
        (50, 5, 49),
        (48, 5, 49),
        (100, 50, 105),
        (5, 10, -2),
    ],
)
def test_given_a_device_where_one_move_too_small_when_check_and_cache_values_then_other_positions_returned(
    my_device, initial, min, home
):
    RE = RunEngine(call_returns_result=True)

    set_mock_value(my_device.x.user_readback, initial)
    set_mock_value(my_device.y.user_readback, 200)

    motors_and_positions: Dict[Motor, float] = RE(
        _check_and_cache_values(my_device, min, 1000, home_position=home)
    ).plan_result  # type: ignore
    cached_positions = motors_and_positions.values()

    assert len(cached_positions) == 1
    assert list(motors_and_positions.keys())[0] == my_device.y
    assert list(cached_positions)[0] == 200


def test_given_a_device_where_all_moves_too_small_when_check_and_cache_values_then_no_positions_returned(
    my_device,
):
    RE = RunEngine(call_returns_result=True)

    set_mock_value(my_device.x.user_readback, 10)
    set_mock_value(my_device.y.user_readback, 20)

    motors_and_positions: Dict[Motor, float] = RE(
        _check_and_cache_values(my_device, 40, 1000)
    ).plan_result  # type: ignore
    cached_positions = motors_and_positions.values()

    assert len(cached_positions) == 0


@pytest.mark.parametrize(
    "initial_x, initial_y, home",
    [
        (10, 20, 0),
        (150, 40, 95),
        (-56, 50, 78),
        (74, -89, -2),
    ],
)
def test_when_home_and_reset_wrapper_called_with_null_plan_then_motos_homed_and_reset(
    RE, my_device, initial_x, initial_y, home
):
    def my_plan():
        yield from bps.null()

    patch_motor(my_device.x, initial_x)
    patch_motor(my_device.y, initial_y)

    RE(
        home_and_reset_wrapper(
            my_plan(),
            my_device,
            home,
            0,
            1000,
        )
    )

    get_mock_put(my_device.x.user_setpoint).assert_has_calls(
        [call(home, wait=ANY, timeout=ANY), call(initial_x, wait=ANY, timeout=ANY)]
    )

    get_mock_put(my_device.y.user_setpoint).assert_has_calls(
        [call(home, wait=ANY, timeout=ANY), call(initial_y, wait=ANY, timeout=ANY)]
    )


@pytest.mark.parametrize(
    "initial, min, home",
    [
        (50, 5, 49),
        (48, 5, 49),
        (100, 50, 105),
        (5, 10, -2),
    ],
)
def test_given_motors_already_close_to_home_when_home_and_reset_wrapper_called_then_motors_do_not_move(
    RE, my_device, initial, home, min
):
    def my_plan():
        yield from bps.null()

    patch_motor(my_device.x, initial)
    patch_motor(my_device.y, initial)

    RE(
        home_and_reset_wrapper(
            my_plan(),
            my_device,
            home,
            min,
            1000,
        )
    )

    get_mock_put(my_device.x.user_setpoint).assert_not_called()
    get_mock_put(my_device.y.user_setpoint).assert_not_called()


@pytest.mark.parametrize(
    "initial_x, initial_y, max, home",
    [
        (1000, 2, 5, 0),
        (2, -1000, 5, 0),
        (90, -1000, 40, 0),
        (60, 500, 40, 50),
        (60, 141, 40, 100),
        (7, -8, 10, 5),
    ],
)
def test_given_an_axis_out_of_range_when_home_and_reset_wrapper_called_then_throws_and_no_motion(
    RE, my_device, initial_x, initial_y, max, home
):
    def my_plan():
        yield from bps.null()

    patch_motor(my_device.x, initial_x)
    patch_motor(my_device.y, initial_y)

    with pytest.raises(MoveTooLarge):
        RE(
            home_and_reset_wrapper(
                my_plan(),
                my_device,
                home,
                0,
                max,
            )
        )

    get_mock_put(my_device.x.user_setpoint).assert_not_called()
    get_mock_put(my_device.y.user_setpoint).assert_not_called()


def test_given_plan_fails_reset_still(RE, my_device):
    initial_x, initial_y, home = 10, 20, 6

    def my_plan():
        yield from bps.null()
        raise Exception()

    patch_motor(my_device.x, initial_x)
    patch_motor(my_device.y, initial_y)

    with pytest.raises(Exception):
        RE(
            home_and_reset_wrapper(
                my_plan(),
                my_device,
                home,
                0,
                1000,
            )
        )

    get_mock_put(my_device.x.user_setpoint).assert_has_calls(
        [call(home, wait=ANY, timeout=ANY), call(initial_x, wait=ANY, timeout=ANY)]
    )

    get_mock_put(my_device.y.user_setpoint).assert_has_calls(
        [call(home, wait=ANY, timeout=ANY), call(initial_y, wait=ANY, timeout=ANY)]
    )


@pytest.mark.parametrize(
    "move_that_failed",
    ["x", "y"],
)
def test_given_move_to_home_fails_reset_still(RE, my_device, move_that_failed):
    initial_x, initial_y, home = 10, 20, 6

    def my_plan():
        # This will never get called as fails before
        yield from bps.abs_set(my_device, 45)

    patch_motor(my_device.x, initial_x)
    patch_motor(my_device.y, initial_y)
    get_mock_put(
        getattr(my_device, move_that_failed).user_setpoint
    ).side_effect = Exception()

    with pytest.raises(Exception):
        RE(
            home_and_reset_wrapper(
                my_plan(),
                my_device,
                home,
                0,
                1000,
            )
        )

    get_mock_put(my_device.x.user_setpoint).assert_has_calls(
        [call(home, wait=ANY, timeout=ANY), call(initial_x, wait=ANY, timeout=ANY)]
    )

    get_mock_put(my_device.y.user_setpoint).assert_has_calls(
        [call(home, wait=ANY, timeout=ANY), call(initial_y, wait=ANY, timeout=ANY)]
    )
