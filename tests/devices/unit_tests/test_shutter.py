import pytest
from ophyd_async.core import DeviceCollector, callback_on_mock_put, set_mock_value

from dodal.devices.shutter import Shutter, ShutterSetState, ShutterState


@pytest.fixture
async def sim_shutter():
    async with DeviceCollector(mock=True):
        sim_shutter: Shutter = Shutter(
            prefix="sim_shutter",
            name="shutter",
        )
    return sim_shutter


async def test_set_shutter_open(sim_shutter: Shutter):
    desired_state: ShutterSetState = ShutterSetState.OPEN

    def set_correct_mock_value(*args, **kwargs):
        set_mock_value(sim_shutter.position_readback, ShutterState.OPEN)

    callback_on_mock_put(sim_shutter.position_set, set_correct_mock_value)
    await sim_shutter.set(desired_state)
    reading = await sim_shutter.read()

    shutter_position = reading.get("shutter-position_readback", {})
    assert (
        shutter_position["value"] is ShutterState.OPEN
    ), f"Unexpected value: {shutter_position['value']}"


async def test_set_shutter_close(sim_shutter: Shutter):
    desired_state: ShutterSetState = ShutterSetState.CLOSE

    def set_correct_mock_value(*args, **kwargs):
        set_mock_value(sim_shutter.position_readback, ShutterState.CLOSED)

    callback_on_mock_put(sim_shutter.position_set, set_correct_mock_value)
    await sim_shutter.set(desired_state)
    reading = await sim_shutter.read()

    shutter_position = reading.get("shutter-position_readback", {})
    assert (
        shutter_position["value"] is ShutterState.CLOSED
    ), f"Unexpected value: {shutter_position['value']}"
