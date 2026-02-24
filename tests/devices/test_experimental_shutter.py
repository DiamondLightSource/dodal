import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.experimental_shutter import ExperimentalShutter, InterlockState
from dodal.devices.hutch_shutter import ShutterState


@pytest.fixture
async def exp_shutter() -> ExperimentalShutter:
    async with init_devices(mock=True):
        exp_shutter = ExperimentalShutter("TEST:")
    return exp_shutter


async def test_shutter_readable(exp_shutter: ExperimentalShutter):
    await assert_reading(
        exp_shutter,
        {
            f"{exp_shutter.name}-interlock": partial_reading(InterlockState.FAILED),
            f"{exp_shutter.name}-status": partial_reading(ShutterState.FAULT),
        },
    )
