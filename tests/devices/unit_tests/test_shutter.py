import pytest
from ophyd_async.core import DeviceCollector, callback_on_mock_put, set_mock_value

from dodal.devices.zebra_controlled_shutter import (
    ZebraShutter,
    ZebraShutterState,
)


@pytest.fixture
async def sim_shutter():
    async with DeviceCollector(mock=True):
        sim_shutter: ZebraShutter = ZebraShutter(
            prefix="sim_shutter",
            name="shutter",
        )
    return sim_shutter


async def test_set_shutter_open(sim_shutter: ZebraShutter):
    desired_state = ZebraShutterState.OPEN

    def set_correct_mock_value(*args, **kwargs):
        set_mock_value(sim_shutter.position_readback, ZebraShutterState.OPEN)

    callback_on_mock_put(sim_shutter.position_set, set_correct_mock_value)
    await sim_shutter.set(desired_state)
    reading = await sim_shutter.read()

    shutter_position = reading.get("shutter-position_readback", {})
    assert (
        shutter_position["value"] is ZebraShutterState.OPEN
    ), f"Unexpected value: {shutter_position['value']}"


async def test_set_shutter_close(sim_shutter: ZebraShutter):
    desired_state = ZebraShutterState.CLOSE

    def set_correct_mock_value(*args, **kwargs):
        set_mock_value(sim_shutter.position_readback, ZebraShutterState.CLOSE)

    callback_on_mock_put(sim_shutter.position_set, set_correct_mock_value)
    await sim_shutter.set(desired_state)
    reading = await sim_shutter.read()

    shutter_position = reading.get("shutter-position_readback", {})
    assert (
        shutter_position["value"] is ZebraShutterState.CLOSE
    ), f"Unexpected value: {shutter_position['value']}"
