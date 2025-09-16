import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import callback_on_mock_put, set_mock_value

from dodal.devices.zebra.zebra_controlled_shutter import (
    ZebraShutter,
    ZebraShutterControl,
    ZebraShutterState,
)


@pytest.fixture
async def sim_shutter():
    async with init_devices(mock=True):
        sim_shutter = ZebraShutter(
            prefix="sim_shutter",
            name="shutter",
        )

    def propagate_status(value: ZebraShutterState, *args, **kwargs):
        set_mock_value(sim_shutter.position_readback, value)

    callback_on_mock_put(sim_shutter._manual_position_setpoint, propagate_status)
    return sim_shutter


@pytest.mark.parametrize("new_state", [ZebraShutterState.OPEN, ZebraShutterState.CLOSE])
async def test_set_shutter_open(
    sim_shutter: ZebraShutter, new_state: ZebraShutterState
):
    await sim_shutter.set(new_state)
    reading = await sim_shutter.read()

    shutter_position = reading.get("shutter-position_readback", {})
    assert shutter_position["value"] is new_state, (
        f"Unexpected value: {shutter_position['value']}"
    )


async def test_given_shutter_in_auto_then_when_set_raises(sim_shutter: ZebraShutter):
    set_mock_value(sim_shutter.control_mode, ZebraShutterControl.AUTO)
    with pytest.raises(UserWarning):
        await sim_shutter.set(ZebraShutterState.OPEN)
