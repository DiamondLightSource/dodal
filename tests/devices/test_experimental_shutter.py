from unittest.mock import call

import bluesky.plan_stubs as bps
import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import (
    get_mock_put,
    init_devices,
    set_mock_value,
)
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.experimental_shutter import ExperimentalShutter, InterlockState
from dodal.devices.hutch_shutter import ShutterDemand, ShutterState


@pytest.fixture
async def exp_shutter() -> ExperimentalShutter:
    async with init_devices(mock=True):
        exp_shutter = ExperimentalShutter("TEST:")

    def completed():
        pass

    mock_put = get_mock_put(exp_shutter.control)
    mock_put.return_value = completed()
    return exp_shutter


async def test_shutter_readable(exp_shutter: ExperimentalShutter):
    await assert_reading(
        exp_shutter,
        {
            f"{exp_shutter.name}-interlock": partial_reading(InterlockState.FAILED),
            f"{exp_shutter.name}-status": partial_reading(ShutterState.FAULT),
        },
    )


@pytest.mark.parametrize(
    "demand, expected_calls, expected_state",
    [
        (
            ShutterDemand.OPEN,
            [ShutterDemand.RESET, ShutterDemand.OPEN],
            ShutterState.OPEN,
        ),
        (ShutterDemand.CLOSE, [ShutterDemand.CLOSE], ShutterState.CLOSED),
        (ShutterDemand.RESET, [ShutterDemand.RESET], ShutterState.CLOSED),
    ],
)
async def test_shutter_set_open_call_list(
    exp_shutter: ExperimentalShutter,
    run_engine: RunEngine,
    demand: ShutterDemand,
    expected_calls: list[ShutterDemand],
    expected_state: ShutterState,
):
    set_mock_value(exp_shutter.status, expected_state)
    run_engine(bps.abs_set(exp_shutter, demand, wait=True))
    mock_put = get_mock_put(exp_shutter.control)
    mock_put.assert_has_calls([call(i, wait=True) for i in expected_calls])
