from unittest.mock import ANY, MagicMock, call, patch

import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from bluesky.utils import FailedStatus
from ophyd_async.core import Device, init_devices, soft_signal_rw
from ophyd_async.epics.motor import Motor
from ophyd_async.testing import (
    get_mock_put,
    set_mock_value,
)

from dodal.devices.util.test_utils import patch_motor
from dodal.plan_stubs.motor_utils import (
    MoveTooLarge,
    check_and_cache_values,
    home_and_reset_wrapper,
)


class DeviceWithOnlyMotors(Device):
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
    with init_devices(mock=True):
        my_device = DeviceWithOnlyMotors()
    return my_device


@pytest.mark.parametrize(
    "device_type",
    [DeviceWithOnlyMotors, DeviceWithNoMotors, DeviceWithSomeMotors],
)
@patch("dodal.plan_stubs.motor_utils.move_and_reset_wrapper")
def test_given_types_of_device_when_home_and_reset_wrapper_called_then_motors_and_zeros_passed_to_move_and_reset_wrapper(
    patch_move_and_reset, device_type, RE
):
    with init_devices(mock=True):
        device = device_type()
    home_and_reset_wrapper(MagicMock(), device, 0, 0)

    home_positions = patch_move_and_reset.call_args.args[1]
    assert home_positions == dict.fromkeys(device.motors, 0.0)


def test_given_a_device_when_check_and_cache_values_then_motor_values_returned(
    my_device,
):
    RE = RunEngine(call_returns_result=True)

    for i, motor in enumerate(my_device.motors, start=1):
        set_mock_value(motor.user_readback, i * 100)

    motors_and_positions: dict[Motor, float] = RE(
        check_and_cache_values(dict.fromkeys(my_device.motors, 0.0), 0, 1000)
    ).plan_result  # type: ignore
    cached_positions = motors_and_positions.values()

    assert len(cached_positions) == len(my_device.motors)
    for i, cached_position in enumerate(cached_positions, start=1):
        assert cached_position, i * 100


@pytest.mark.parametrize(
    "initial, max, new_position",
    [
        (200, 100, 0),
        (-200, 100, 0),
        (-200, 100, -50),
        (-200, 100, 50),
    ],
)
def test_given_a_device_with_a_too_large_move_when_check_and_cache_values_then_exception_thrown(
    RE, my_device: DeviceWithOnlyMotors, initial, max, new_position: float
):
    set_mock_value(my_device.x.user_readback, 10)
    set_mock_value(my_device.y.user_readback, initial)

    motors_and_positions = dict.fromkeys(my_device.motors, new_position)

    with pytest.raises(MoveTooLarge) as e:
        RE(check_and_cache_values(motors_and_positions, 0, max))
        assert e.value.axis == my_device.y
        assert e.value.maximum_move == max


@pytest.mark.parametrize(
    "initial, min, new_position",
    [
        (50, 5, 49),
        (48, 5, 49),
        (100, 50, 105),
        (5, 10, -2),
    ],
)
def test_given_a_device_where_one_move_too_small_when_check_and_cache_values_then_other_positions_returned(
    my_device: DeviceWithOnlyMotors, initial, min, new_position: float
):
    RE = RunEngine(call_returns_result=True)

    set_mock_value(my_device.x.user_readback, initial)
    set_mock_value(my_device.y.user_readback, 200)

    motors_and_new_positions = dict.fromkeys(my_device.motors, new_position)

    motors_and_positions: dict[Motor, float] = RE(
        check_and_cache_values(motors_and_new_positions, min, 1000)
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

    motors_and_new_positions = dict.fromkeys(my_device.motors, 0.0)

    motors_and_positions: dict[Motor, float] = RE(
        check_and_cache_values(motors_and_new_positions, 40, 1000)
    ).plan_result  # type: ignore
    cached_positions = motors_and_positions.values()

    assert len(cached_positions) == 0


@pytest.mark.parametrize(
    "initial_x, initial_y",
    [
        (10, 20),
        (150, 40),
        (-56, 50),
        (74, -89),
    ],
)
def test_when_home_and_reset_wrapper_called_with_null_plan_then_motors_homed_and_reset(
    RE,
    my_device,
    initial_x,
    initial_y,
):
    def my_plan():
        yield from bps.null()

    patch_motor(my_device.x, initial_x)
    patch_motor(my_device.y, initial_y)

    RE(
        home_and_reset_wrapper(
            my_plan(),
            my_device,
            0,
            1000,
        )
    )

    get_mock_put(my_device.x.user_setpoint).assert_has_calls(
        [call(0, wait=ANY), call(initial_x, wait=ANY)]
    )

    get_mock_put(my_device.y.user_setpoint).assert_has_calls(
        [call(0, wait=ANY), call(initial_y, wait=ANY)]
    )


@pytest.mark.parametrize(
    "initial, min",
    [
        (1, 5),
        (-1, 5),
        (-5, 50),
        (7, 10),
    ],
)
def test_given_motors_already_close_to_home_when_home_and_reset_wrapper_called_then_motors_do_not_move(
    RE, my_device, initial, min
):
    def my_plan():
        yield from bps.null()

    patch_motor(my_device.x, initial)
    patch_motor(my_device.y, initial)

    RE(
        home_and_reset_wrapper(
            my_plan(),
            my_device,
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


class MyException(Exception):
    pass


def test_given_home_and_reset_inner_plan_fails_reset_still(RE, my_device):
    initial_x, initial_y = 10, 20

    def my_plan():
        yield from bps.null()
        raise MyException()

    patch_motor(my_device.x, initial_x)
    patch_motor(my_device.y, initial_y)

    with pytest.raises(MyException):
        RE(
            home_and_reset_wrapper(
                my_plan(),
                my_device,
                0,
                1000,
            )
        )

    get_mock_put(my_device.x.user_setpoint).assert_has_calls(
        [call(0.0, wait=ANY), call(initial_x, wait=ANY)]
    )

    get_mock_put(my_device.y.user_setpoint).assert_has_calls(
        [call(0.0, wait=ANY), call(initial_y, wait=ANY)]
    )


@pytest.mark.parametrize(
    "move_that_failed",
    ["x", "y"],
)
def test_given_move_to_home_fails_reset_still(RE, my_device, move_that_failed):
    initial_x, initial_y = 10, 20

    def my_plan():
        # This will never get called as fails before
        yield from bps.abs_set(my_device, 45)

    patch_motor(my_device.x, initial_x)
    patch_motor(my_device.y, initial_y)
    get_mock_put(
        getattr(my_device, move_that_failed).user_setpoint
    ).side_effect = MyException()

    with pytest.raises(FailedStatus) as e:
        RE(
            home_and_reset_wrapper(
                my_plan(),
                my_device,
                0,
                1000,
            )
        )

    assert isinstance(e.value.__cause__, MyException)

    get_mock_put(my_device.x.user_setpoint).assert_has_calls(
        [call(0.0, wait=ANY), call(initial_x, wait=ANY)]
    )

    get_mock_put(my_device.y.user_setpoint).assert_has_calls(
        [call(0.0, wait=ANY), call(initial_y, wait=ANY)]
    )
