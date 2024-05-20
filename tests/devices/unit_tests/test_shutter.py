import pytest
from ophyd_async.core import DeviceCollector

from dodal.devices.shutter import OpenStateReadback, Shutter


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
        (OpenStateReadback.OPEN),
        (OpenStateReadback.CLOSED),
    ],
)
async def test_set_opens_and_closes_shutter(
    state: OpenStateReadback, sim_shutter: Shutter
):
    status = sim_shutter.position_readback.set(state)
    assert not status.done
    reading = await sim_shutter.read()

    shutter_position = reading.get("shutter-position", {})
    assert (
        shutter_position["value"] is state
    ), f"Unexpected value: {shutter_position['value']}"
    await status
