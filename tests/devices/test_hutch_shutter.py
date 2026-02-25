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
    HutchInterlock,
    HutchInterlockPSS,
    HutchShutter,
    InterlockState,
    ShutterDemand,
    ShutterNotSafeToOperateError,
    ShutterState,
)


@pytest.fixture
async def interlock_pss() -> HutchInterlockPSS:
    async with init_devices(mock=True):
        interlock_pss = HutchInterlockPSS(bl_prefix="TEST")
    return interlock_pss


@pytest.fixture
async def interlock() -> HutchInterlock:
    async with init_devices(mock=True):
        interlock_pss = HutchInterlock(bl_prefix="TEST")
    return interlock_pss


@pytest.fixture
async def fake_shutter(interlock_pss: HutchInterlockPSS) -> HutchShutter:
    async with init_devices(mock=True):
        shutter = HutchShutter(interlock=interlock_pss, bl_prefix="TEST")

    def set_status(value: ShutterDemand, *args, **kwargs):
        value_sta = ShutterState.OPEN if value == "Open" else ShutterState.CLOSED
        set_mock_value(shutter.status, value_sta)

    callback_on_mock_put(shutter.control, set_status)

    return shutter


def test_shutter_can_be_created(fake_shutter: HutchShutter):
    assert isinstance(fake_shutter, HutchShutter)


async def test_interlock_pss_readable(interlock_pss: HutchInterlockPSS):
    await assert_reading(
        interlock_pss,
        {
            f"{interlock_pss.name}-status": partial_reading(0.0),
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
async def test_interlock_pss_shutter_safe_to_operate_logic(
    interlock_pss: HutchInterlockPSS,
    readback: float,
    expected_state: bool,
):
    set_mock_value(interlock_pss.status, readback)
    assert await interlock_pss.shutter_safe_to_operate() is expected_state


async def test_interlock_readable(interlock: HutchInterlock):
    await assert_reading(
        interlock,
        {
            f"{interlock.name}-status": partial_reading(InterlockState.FAILED),
        },
    )


@pytest.mark.parametrize(
    "readback, expected_state",
    [
        (InterlockState.DISARMED, False),
        (InterlockState.OK, True),
        (InterlockState.FAILED, True),
    ],
)
async def test_interlock_shutter_safe_to_operate_logic(
    interlock: HutchInterlock,
    readback: float,
    expected_state: bool,
):
    set_mock_value(interlock.status, readback)
    assert await interlock.shutter_safe_to_operate() is expected_state


async def test_shutter_readable(fake_shutter: HutchShutter):
    await assert_reading(
        fake_shutter,
        {
            f"{fake_shutter.interlock.name}-status": partial_reading(0.0),
            f"{fake_shutter.name}-status": partial_reading(ShutterState.FAULT),
        },
    )


async def test_shutter_raises_error_on_set_if_hutch_not_interlocked_on_open(
    fake_shutter: HutchShutter,
):
    set_mock_value(fake_shutter.interlock.status, 1)
    assert await fake_shutter.interlock.shutter_safe_to_operate() is False

    with pytest.raises(ShutterNotSafeToOperateError):
        await fake_shutter.set(ShutterDemand.OPEN)


async def test_shutter_does_not_error_on_close_even_if_hutch_not_interlocked(
    fake_shutter: HutchShutter,
):
    set_mock_value(fake_shutter.interlock.status, 1)
    assert await fake_shutter.interlock.shutter_safe_to_operate() is False

    await fake_shutter.set(ShutterDemand.CLOSE)


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
async def test_shutter_operations(
    demand: ShutterDemand,
    expected_calls: list,
    expected_state: ShutterState,
    fake_shutter: HutchShutter,
    run_engine: RunEngine,
):
    set_mock_value(fake_shutter.interlock.status, 0)

    run_engine(bps.abs_set(fake_shutter, demand, wait=True))

    assert await fake_shutter.status.get_value() == expected_state
    mock_shutter_control = get_mock_put(fake_shutter.control)
    mock_shutter_control.assert_has_calls([call(i, wait=True) for i in expected_calls])


@patch("dodal.devices.hutch_shutter.LOGGER")
@patch("dodal.devices.hutch_shutter.TEST_MODE")
async def test_shutter_does_not_operate_in_test_mode(
    patch_test_mode, patch_log, fake_shutter: HutchShutter, run_engine: RunEngine
):
    patch_test_mode.return_value = True
    set_mock_value(fake_shutter.interlock.status, 1)  # Optics hutch open
    set_mock_value(fake_shutter.status, ShutterState.CLOSED)

    run_engine(bps.abs_set(fake_shutter, ShutterDemand.OPEN, wait=True))

    # Assert shutter state didn't change and warning was logged
    patch_log.warning.assert_called_once_with(
        "Running in test mode, will not operate the experiment shutter."
    )
    assert await fake_shutter.status.get_value() == ShutterState.CLOSED
