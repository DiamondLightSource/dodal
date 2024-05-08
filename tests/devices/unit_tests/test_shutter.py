import pytest
from ophyd_async.core import DeviceCollector

from dodal.devices.shutter import OpenState, Shutter


@pytest.fixture
async def sim_shutter():
    async with DeviceCollector(sim=True):
        sim_shutter: Shutter = Shutter(
            prefix="sim_shutter",
            name="shutter",
        )
    return sim_shutter


@pytest.mark.parametrize(
    "state",
    [
        (OpenState.OPEN),
        (OpenState.CLOSE),
    ],
)
async def test_set_opens_and_closes_shutter(state: OpenState, sim_shutter: Shutter):
    status = sim_shutter.set(state)
    assert not status.done
    reading = await sim_shutter.read()

    shutter_position = reading.get("shutter-position", {})
    assert shutter_position["value"] in [
        0,
        1,
    ], f"Unexpected value: {shutter_position['value']}"

    # Assert that 'timestamp' is a float
    assert isinstance(
        shutter_position["timestamp"], float
    ), f"Timestamp is not a float: {type(shutter_position['timestamp'])}"

    # Assert that 'alarm_severity' is 0
    assert shutter_position.get("alarm_severity") is not None, "Alarm severity is None"
    severity = shutter_position["alarm_severity"]  # type: ignore
    assert severity == 0, f"Alarm severity is not 0: {severity}"

    if state == OpenState.CLOSE:
        assert shutter_position["value"] == OpenState.CLOSE
    if state == OpenState.OPEN:
        assert shutter_position["value"] == OpenState.OPEN
