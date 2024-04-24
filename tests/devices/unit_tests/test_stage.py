import pytest
from ophyd_async.core import DeviceCollector

from dodal.devices.stages import ThreeAxisStage


@pytest.fixture
async def sim_three_axis_motor():
    async with DeviceCollector(sim=True):
        sim_three_axis_motor = ThreeAxisStage("BLxx-MO-xx-01:", "sim_three_axis_motor")
        # Signals connected here

    yield sim_three_axis_motor


async def test_there_axis_motor(sim_three_axis_motor: ThreeAxisStage) -> None:
    assert sim_three_axis_motor.name == "sim_three_axis_motor"
    assert sim_three_axis_motor.x.name == "sim_three_axis_motor-x"
    assert sim_three_axis_motor.y.name == "sim_three_axis_motor-y"
    assert sim_three_axis_motor.z.name == "sim_three_axis_motor-z"
