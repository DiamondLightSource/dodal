import pytest
from ophyd_async.core import DeviceCollector
from ophyd_async.testing import set_mock_value

from dodal.devices.attenuator.filter import FilterMotor
from dodal.devices.attenuator.filter_selections import p99StageSelections
from dodal.devices.p99.sample_stage import (
    SampleAngleStage,
)

# Long enough for multiple asyncio event loop cycles to run so
# all the tasks have a chance to run
A_BIT = 0.001


@pytest.fixture
async def sim_sampleAngleStage():
    async with DeviceCollector(mock=True):
        sim_sampleAngleStage = SampleAngleStage(
            "p99-MO-TABLE-01:", name="sim_sampleAngleStage"
        )
        # Signals connected here
    yield sim_sampleAngleStage


@pytest.fixture
async def sim_filter_wheel():
    async with DeviceCollector(mock=True):
        sim_filter_wheel = FilterMotor(
            filter_selections=p99StageSelections,
            prefix="p99-MO-TABLE-01:",
            name="sim_filter_wheel",
        )
    yield sim_filter_wheel


async def test_sampleAngleStage(sim_sampleAngleStage: SampleAngleStage) -> None:
    assert sim_sampleAngleStage.name == "sim_sampleAngleStage"
    assert sim_sampleAngleStage.theta.name == "sim_sampleAngleStage-theta"
    assert sim_sampleAngleStage.roll.name == "sim_sampleAngleStage-roll"
    assert sim_sampleAngleStage.pitch.name == "sim_sampleAngleStage-pitch"


async def test_filter_wheel(sim_filter_wheel: FilterMotor) -> None:
    assert sim_filter_wheel.name == "sim_filter_wheel"
    set_mock_value(sim_filter_wheel.user_setpoint, p99StageSelections.CD25UM)
    assert await sim_filter_wheel.user_setpoint.get_value() == p99StageSelections.CD25UM
