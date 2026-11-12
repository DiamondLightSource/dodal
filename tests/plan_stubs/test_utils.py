from typing import Any

import pytest
from bluesky import RunEngine
from bluesky.run_engine import RunEngineResult
from ophyd_async.core import init_devices
from ophyd_async.epics.motor import OffsetMode, UseSetMode

from dodal.devices.motors import XYStage
from dodal.plan_stubs import state


@pytest.fixture
def xy_stage() -> XYStage:
    with init_devices(mock=True):
        xy_stage = XYStage("TEST:")
    return xy_stage


def assert_result(result, expected: Any):
    if not isinstance(result, RunEngineResult):
        raise ValueError(
            f"Expected type RunEngineResult. Got type {type(result)} instead."
        )

    assert result.plan_result == expected


def test_state_plan_stub_on_motor_reports_back_all_children(
    run_engine: RunEngine, xy_stage: XYStage
):
    result = run_engine(state(xy_stage.x))
    expected = {
        "xy_stage-x": 0.0,
        "xy_stage-x-acceleration_time": 0.0,
        "xy_stage-x-deadband": 0.0,
        "xy_stage-x-dial_high_limit_travel": 0.0,
        "xy_stage-x-dial_low_limit_travel": 0.0,
        "xy_stage-x-encoder_resolution": 0.0,
        "xy_stage-x-high_limit_switch": 0,
        "xy_stage-x-high_limit_travel": 0.0,
        "xy_stage-x-low_limit_switch": 0,
        "xy_stage-x-low_limit_travel": 0.0,
        "xy_stage-x-max_velocity": 1000.0,
        "xy_stage-x-motor_done_move": 1,
        "xy_stage-x-motor_egu": "",
        "xy_stage-x-motor_resolution": 0.0,
        "xy_stage-x-motor_stop": None,
        "xy_stage-x-offset": 0.0,
        "xy_stage-x-offset_freeze_switch": OffsetMode.VARIABLE,
        "xy_stage-x-output_link": "",
        "xy_stage-x-precision": 0,
        "xy_stage-x-set_use_switch": UseSetMode.USE,
        "xy_stage-x-steps_per_revolution": 0,
        "xy_stage-x-units_per_revolution": 0.0,
        "xy_stage-x-user_setpoint": 0.0,
        "xy_stage-x-velocity": 1000.0,
    }
    assert_result(result, expected)


EXPECTED_COMPOSITE = {
    "xy_stage-x": 0.0,
    "xy_stage-x-acceleration_time": 0.0,
    "xy_stage-x-deadband": 0.0,
    "xy_stage-x-dial_high_limit_travel": 0.0,
    "xy_stage-x-dial_low_limit_travel": 0.0,
    "xy_stage-x-encoder_resolution": 0.0,
    "xy_stage-x-high_limit_switch": 0,
    "xy_stage-x-high_limit_travel": 0.0,
    "xy_stage-x-low_limit_switch": 0,
    "xy_stage-x-low_limit_travel": 0.0,
    "xy_stage-x-max_velocity": 1000.0,
    "xy_stage-x-motor_done_move": 1,
    "xy_stage-x-motor_egu": "",
    "xy_stage-x-motor_resolution": 0.0,
    "xy_stage-x-motor_stop": None,
    "xy_stage-x-offset": 0.0,
    "xy_stage-x-offset_freeze_switch": OffsetMode.VARIABLE,
    "xy_stage-x-output_link": "",
    "xy_stage-x-precision": 0,
    "xy_stage-x-set_use_switch": UseSetMode.USE,
    "xy_stage-x-steps_per_revolution": 0,
    "xy_stage-x-units_per_revolution": 0.0,
    "xy_stage-x-user_setpoint": 0.0,
    "xy_stage-x-velocity": 1000.0,
    "xy_stage-y": 0.0,
    "xy_stage-y-acceleration_time": 0.0,
    "xy_stage-y-deadband": 0.0,
    "xy_stage-y-dial_high_limit_travel": 0.0,
    "xy_stage-y-dial_low_limit_travel": 0.0,
    "xy_stage-y-encoder_resolution": 0.0,
    "xy_stage-y-high_limit_switch": 0,
    "xy_stage-y-high_limit_travel": 0.0,
    "xy_stage-y-low_limit_switch": 0,
    "xy_stage-y-low_limit_travel": 0.0,
    "xy_stage-y-max_velocity": 1000.0,
    "xy_stage-y-motor_done_move": 1,
    "xy_stage-y-motor_egu": "",
    "xy_stage-y-motor_resolution": 0.0,
    "xy_stage-y-motor_stop": None,
    "xy_stage-y-offset": 0.0,
    "xy_stage-y-offset_freeze_switch": OffsetMode.VARIABLE,
    "xy_stage-y-output_link": "",
    "xy_stage-y-precision": 0,
    "xy_stage-y-set_use_switch": UseSetMode.USE,
    "xy_stage-y-steps_per_revolution": 0,
    "xy_stage-y-units_per_revolution": 0.0,
    "xy_stage-y-user_setpoint": 0.0,
    "xy_stage-y-velocity": 1000.0,
}


def test_state_plan_stub_on_composite_device_reports_back_all_children(
    run_engine: RunEngine, xy_stage: XYStage
):
    result = run_engine(state(xy_stage))
    assert_result(result, EXPECTED_COMPOSITE)


def test_state_plan_stub_on_many_devices_reports_back_all_children(
    run_engine: RunEngine, xy_stage: XYStage
):
    result = run_engine(state(xy_stage.x, xy_stage.y))
    assert_result(result, EXPECTED_COMPOSITE)
