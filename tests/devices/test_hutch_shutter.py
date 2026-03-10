from unittest.mock import call, patch

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    callback_on_mock_put,
    get_mock_put,
    init_devices,
    set_mock_value,
)
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.hutch_shutter import (
    BaseHutchShutter,
    HutchInterlock,
    HutchShutter,
    InterlockedHutchShutter,
    ShutterDemand,
    ShutterNotSafeToOperateError,
    ShutterState,
)


@pytest.fixture
async def interlock() -> HutchInterlock:
    async with init_devices(mock=True):
        interlock = HutchInterlock(bl_prefix="TEST")
    return interlock


@pytest.fixture
async def fake_interlocked_shutter(
    interlock: HutchInterlock,
) -> InterlockedHutchShutter:
    async with init_devices(mock=True):
        interlocked_shutter = InterlockedHutchShutter(
            bl_prefix="TEST", interlock=interlock
        )

    def set_status(value: ShutterDemand, *args, **kwargs):
        value_sta = ShutterState.OPEN if value == "Open" else ShutterState.CLOSED
        set_mock_value(interlocked_shutter.status, value_sta)

    callback_on_mock_put(interlocked_shutter.control, set_status)

    return interlocked_shutter


@pytest.fixture
async def fake_shutter_without_interlock() -> HutchShutter:
    async with init_devices(mock=True):
        shutter = HutchShutter(bl_prefix="TEST")

    def set_status(value: ShutterDemand, *args, **kwargs):
        value_sta = ShutterState.OPEN if value == "Open" else ShutterState.CLOSED
        set_mock_value(shutter.status, value_sta)

    callback_on_mock_put(shutter.control, set_status)

    return shutter


def test_shutter_can_be_created(fake_shutter_without_interlock: HutchShutter):
    assert isinstance(fake_shutter_without_interlock, BaseHutchShutter)


def test_interlocked_shutter_can_be_created(
    fake_interlocked_shutter: InterlockedHutchShutter,
):
    assert isinstance(fake_interlocked_shutter, BaseHutchShutter)


async def test_interlock_is_readable(interlock: HutchInterlock):
    await assert_reading(
        interlock,
        {
            f"{interlock.name}-status": partial_reading(0.0),
        },
    )


@pytest.mark.parametrize(
    "readback, expected_state",
    [
        (0.0, True),
        (1.0, False),
        (7.0, False),
    ],
)
async def test_hutch_interlock_safe_to_operate_logic(
    interlock: HutchInterlock,
    readback: float,
    expected_state: bool,
):
    set_mock_value(interlock.status, readback)
    assert await interlock.shutter_safe_to_operate() is expected_state


async def test_shutter_readable(fake_shutter_without_interlock: HutchShutter):
    result = {
        f"{fake_shutter_without_interlock.name}-status": partial_reading(
            ShutterState.FAULT
        ),
    }
    await assert_reading(
        fake_shutter_without_interlock,
        result,
    )


async def test_interlocked_shutter_readable(
    fake_interlocked_shutter: InterlockedHutchShutter,
):
    result = {
        f"{fake_interlocked_shutter.name}-status": partial_reading(ShutterState.FAULT),
    }
    result[f"{fake_interlocked_shutter.interlock.name}-status"] = partial_reading(0.0)
    await assert_reading(
        fake_interlocked_shutter,
        result,
    )


async def test_interlocked_shutter_raises_error_on_open_if_hutch_not_locked(
    fake_interlocked_shutter: InterlockedHutchShutter,
    interlock: HutchInterlock,
):
    set_mock_value(interlock.status, 1)  # hutch is unlocked
    assert await interlock.shutter_safe_to_operate() is False

    with pytest.raises(ShutterNotSafeToOperateError):
        await fake_interlocked_shutter.set(ShutterDemand.OPEN)


async def test_interlocked_shutter_does_not_error_on_close_even_if_hutch_not_locked(
    fake_interlocked_shutter: InterlockedHutchShutter,
    interlock: HutchInterlock,
):
    set_mock_value(interlock.status, 1)  # hutch is unlocked
    assert await interlock.shutter_safe_to_operate() is False

    await fake_interlocked_shutter.set(ShutterDemand.CLOSE)


async def test_shutter_without_interlock_does_not_raise_error_on_open(
    fake_shutter_without_interlock: HutchShutter,
):
    await fake_shutter_without_interlock.set(ShutterDemand.OPEN)
    mock_shutter_control = get_mock_put(fake_shutter_without_interlock.control)
    mock_shutter_control.assert_has_calls(
        [call(i) for i in [ShutterDemand.RESET, ShutterDemand.OPEN]]
    )


async def test_shutter_without_interlock_does_not_error_on_close(
    fake_shutter_without_interlock: HutchShutter,
):
    await fake_shutter_without_interlock.set(ShutterDemand.CLOSE)


@pytest.mark.parametrize(
    "demand, expected_calls, expected_state",
    [
        (
            ShutterDemand.OPEN,
            [ShutterDemand.RESET, ShutterDemand.OPEN],
            ShutterState.OPEN,
        ),
        (ShutterDemand.CLOSE, [ShutterDemand.CLOSE], ShutterState.CLOSED),
    ],
)
async def test_interlocked_shutter_operations(
    demand: ShutterDemand,
    expected_calls: list,
    expected_state: ShutterState,
    fake_interlocked_shutter: HutchShutter,
    interlock: HutchInterlock,
    run_engine: RunEngine,
):
    set_mock_value(interlock.status, 0)  # hutch is locked

    run_engine(bps.abs_set(fake_interlocked_shutter, demand, wait=True))

    assert await fake_interlocked_shutter.status.get_value() == expected_state
    mock_shutter_control = get_mock_put(fake_interlocked_shutter.control)
    mock_shutter_control.assert_has_calls([call(i) for i in expected_calls])


@pytest.mark.parametrize(
    "demand, expected_calls, expected_state",
    [
        (
            ShutterDemand.OPEN,
            [ShutterDemand.RESET, ShutterDemand.OPEN],
            ShutterState.OPEN,
        ),
        (ShutterDemand.CLOSE, [ShutterDemand.CLOSE], ShutterState.CLOSED),
    ],
)
async def test_shutter_without_interlock_operations(
    demand: ShutterDemand,
    expected_calls: list,
    expected_state: ShutterState,
    fake_shutter_without_interlock: HutchShutter,
    run_engine: RunEngine,
):
    run_engine(bps.abs_set(fake_shutter_without_interlock, demand, wait=True))

    assert await fake_shutter_without_interlock.status.get_value() == expected_state
    mock_shutter_control = get_mock_put(fake_shutter_without_interlock.control)
    mock_shutter_control.assert_has_calls([call(i) for i in expected_calls])


@patch("dodal.devices.hutch_shutter.LOGGER")
@patch("dodal.devices.hutch_shutter.TEST_MODE")
async def test_that_in_test_mode_interlocked_shutter_logs_warning_when_shutter_open_attempted(
    patch_test_mode,
    patch_log,
    fake_interlocked_shutter: InterlockedHutchShutter,
    interlock: HutchInterlock,
    run_engine: RunEngine,
):
    patch_test_mode.return_value = True
    set_mock_value(interlock.status, 1)  # hutch is unlocked
    set_mock_value(fake_interlocked_shutter.status, ShutterState.CLOSED)

    run_engine(bps.abs_set(fake_interlocked_shutter, ShutterDemand.OPEN, wait=True))

    # Assert shutter state didn't change and warning was logged
    patch_log.warning.assert_called_once_with(
        "Running in test mode, will not operate the experiment shutter."
    )


@patch("dodal.devices.hutch_shutter.TEST_MODE")
async def test_that_in_test_mode_that_interlocked_shutter_does_not_talk_to_shutter_control_when_hutch_unlocked(
    patch_test_mode,
    fake_interlocked_shutter: InterlockedHutchShutter,
    interlock: HutchInterlock,
    run_engine: RunEngine,
):
    patch_test_mode.return_value = True
    set_mock_value(interlock.status, 1)  # hutch is unlocked
    set_mock_value(fake_interlocked_shutter.status, ShutterState.CLOSED)

    run_engine(bps.abs_set(fake_interlocked_shutter, ShutterDemand.OPEN, wait=True))

    mock_shutter_control = get_mock_put(fake_interlocked_shutter.control)
    mock_shutter_control.assert_not_called()


@patch("dodal.devices.hutch_shutter.TEST_MODE")
async def test_that_in_test_mode_that_interlocked_shutter_does_not_talk_to_shutter_control_even_if_hutch_locked(
    patch_test_mode,
    fake_interlocked_shutter: InterlockedHutchShutter,
    interlock: HutchInterlock,
    run_engine: RunEngine,
):
    patch_test_mode.return_value = True
    set_mock_value(interlock.status, 0)  # hutch is locked
    set_mock_value(fake_interlocked_shutter.status, ShutterState.CLOSED)

    run_engine(bps.abs_set(fake_interlocked_shutter, ShutterDemand.OPEN, wait=True))

    mock_shutter_control = get_mock_put(fake_interlocked_shutter.control)
    mock_shutter_control.assert_not_called()


@patch("dodal.devices.hutch_shutter.LOGGER")
@patch("dodal.devices.hutch_shutter.TEST_MODE")
async def test_that_in_test_mode_closed_shutter_without_interlock_logs_warning(
    patch_test_mode,
    patch_log,
    fake_shutter_without_interlock: HutchShutter,
    run_engine: RunEngine,
):
    patch_test_mode.return_value = True
    set_mock_value(fake_shutter_without_interlock.status, ShutterState.CLOSED)

    run_engine(
        bps.abs_set(fake_shutter_without_interlock, ShutterDemand.OPEN, wait=True)
    )

    # Assert shutter state didn't change and warning was logged
    patch_log.warning.assert_called_once_with(
        "Running in test mode, will not operate the experiment shutter."
    )


@patch("dodal.devices.hutch_shutter.TEST_MODE")
async def test_that_in_test_mode_closed_shutter_without_interlock_does_not_talk_to_shutter_control(
    patch_test_mode,
    fake_shutter_without_interlock: HutchShutter,
    run_engine: RunEngine,
):
    patch_test_mode.return_value = True
    set_mock_value(fake_shutter_without_interlock.status, ShutterState.CLOSED)

    run_engine(
        bps.abs_set(fake_shutter_without_interlock, ShutterDemand.OPEN, wait=True)
    )

    mock_shutter_control = get_mock_put(fake_shutter_without_interlock.control)
    mock_shutter_control.assert_not_called()
