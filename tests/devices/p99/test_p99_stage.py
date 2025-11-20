import pytest
from ophyd_async.core import init_devices, set_mock_value

from dodal.devices.attenuator.filter import FilterMotor
from dodal.devices.attenuator.filter_selections import P99FilterSelections
from dodal.devices.p99.sample_stage import (
    SampleAngleStage,
)

# Long enough for multiple asyncio event loop cycles to run so
# all the tasks have a chance to run
A_BIT = 0.001


@pytest.fixture
async def sim_sample_angle_stage():
    async with init_devices(mock=True):
        sim_sample_angle_stage = SampleAngleStage(
            "p99-MO-TABLE-01:", name="sim_sample_angle_stage"
        )
        # Signals connected here
    yield sim_sample_angle_stage


@pytest.fixture
async def sim_filter_wheel():
    async with init_devices(mock=True):
        sim_filter_wheel = FilterMotor(
            "p99-MO-TABLE-01:",
            P99FilterSelections,
        )
    yield sim_filter_wheel


async def test_sample_angle_stage(sim_sample_angle_stage: SampleAngleStage) -> None:
    assert sim_sample_angle_stage.name == "sim_sample_angle_stage"
    assert sim_sample_angle_stage.theta.name == "sim_sample_angle_stage-theta"
    assert sim_sample_angle_stage.roll.name == "sim_sample_angle_stage-roll"
    assert sim_sample_angle_stage.pitch.name == "sim_sample_angle_stage-pitch"


async def test_filter_wheel(sim_filter_wheel: FilterMotor) -> None:
    assert sim_filter_wheel.name == "sim_filter_wheel"
    set_mock_value(sim_filter_wheel.user_setpoint, P99FilterSelections.CD25UM)
    assert (
        await sim_filter_wheel.user_setpoint.get_value() == P99FilterSelections.CD25UM
    )
