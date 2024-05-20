import pytest
from ophyd_async.core import DeviceCollector

from dodal.devices.shutter import Shutter, ShutterState, ShutterSetState


@pytest.fixture
async def sim_shutter():
    async with DeviceCollector(mock=True):
        sim_shutter: Shutter = Shutter(
            prefix="sim_shutter",
            name="shutter",
        )
    return sim_shutter


@pytest.mark.parametrize(
    "state",
    [
        (ShutterSetState.OPEN),
        (ShutterSetState.CLOSED),
    ],
)
async def test_set_opens_and_closes_shutter(state: ShutterState, sim_shutter: Shutter):
    status = sim_shutter.set(state)
    reading = await sim_shutter.read()

    shutter_position = reading.get("shutter-position", {})
    assert (
        shutter_position["value"] is state
    ), f"Unexpected value: {shutter_position['value']}"
    await status
