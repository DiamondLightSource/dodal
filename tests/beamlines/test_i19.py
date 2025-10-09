import asyncio

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.testing import callback_on_mock_put, set_mock_value

from dodal.beamline_specific_utils.i19 import HutchState
from dodal.beamlines.i19_1 import access_control, shutter
from dodal.devices.hutch_shutter import (
    HUTCH_SAFE_FOR_OPERATIONS,
    HutchShutter,
    ShutterDemand,
    ShutterState,
)
from dodal.devices.i19.hutch_access import HutchAccessControl


@pytest.fixture
def i19_1_shutter(
    RE: RunEngine, i19_access_control: HutchAccessControl
) -> HutchShutter:
    device = shutter(mock=True, connect_immediately=True)
    set_mock_value(device.status, ShutterState.CLOSED)
    set_mock_value(device.interlock.status, HUTCH_SAFE_FOR_OPERATIONS)

    def open_shutter(demand: ShutterDemand, wait: bool):
        match demand:
            case ShutterDemand.OPEN:
                set_mock_value(device.status, ShutterState.OPEN)
            case ShutterDemand.CLOSE:
                set_mock_value(device.status, ShutterState.CLOSED)

    callback_on_mock_put(device.control, open_shutter)
    return shutter(mock=True)


@pytest.fixture
def i19_access_control(RE: RunEngine) -> HutchAccessControl:
    return access_control(mock=True, connect_immediately=True)


@pytest.mark.parametrize("active_hutch", [HutchState.EH1, HutchState.EH2])
async def test_device_locking(
    active_hutch: HutchState,
    i19_access_control: HutchAccessControl,
    i19_1_shutter: HutchShutter,
):
    set_mock_value(i19_access_control.active_hutch, active_hutch.value)

    assert await i19_1_shutter.status.get_value() == ShutterState.CLOSED
    assert await i19_1_shutter.interlock.status.get_value() == HUTCH_SAFE_FOR_OPERATIONS

    set_status = i19_1_shutter.set(ShutterDemand.OPEN)

    while not set_status.done:
        # Allow time for the set to be scheduled?
        await asyncio.sleep(0.01)

    shutter_state = await i19_1_shutter.status.get_value()

    if active_hutch == HutchState.EH1:
        assert shutter_state is ShutterState.OPEN
    else:
        assert shutter_state is ShutterState.CLOSED
