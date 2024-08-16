from unittest.mock import ANY

import pytest
from ophyd_async.core import DeviceCollector, assert_reading, set_mock_value

from dodal.devices.pressure_jump_cell import (
    BusyState,
    FastValveState,
    LimitSwitchState,
    PressureJumpCell,
    PumpMotorDirectionState,
    TimerState,
    ValveState,
)


@pytest.fixture
async def cell() -> PressureJumpCell:
    async with DeviceCollector(mock=True):
        pjump = PressureJumpCell("DEMO-PJUMPCELL-01:")

    return pjump


async def test_reading_pjumpcell_includes_read_fields_valves(
    cell: PressureJumpCell,
):
    set_mock_value(cell.all_valves_control.valve_states[1], ValveState.CLOSED)
    set_mock_value(cell.all_valves_control.valve_states[3], ValveState.OPEN)
    set_mock_value(
        cell.all_valves_control.fast_valve_states[5],
        FastValveState.CLOSED_ARMED,
    )
    set_mock_value(
        cell.all_valves_control.fast_valve_states[6], FastValveState.OPEN_ARMED
    )

    await assert_reading(
        cell.all_valves_control,
        {
            "pjump-all_valves_control-valve_states-1": {
                "value": ValveState.CLOSED,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-all_valves_control-valve_states-3": {
                "value": ValveState.OPEN,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-all_valves_control-fast_valve_states-5": {
                "value": FastValveState.CLOSED_ARMED,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-all_valves_control-fast_valve_states-6": {
                "value": FastValveState.OPEN_ARMED,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )


async def test_reading_pjumpcell_includes_read_fields_pump(
    cell: PressureJumpCell,
):
    set_mock_value(cell.pump.pump_position, 100)
    set_mock_value(cell.pump.pump_forward_limit, LimitSwitchState.OFF)
    set_mock_value(cell.pump.pump_backward_limit, LimitSwitchState.ON)
    set_mock_value(
        cell.pump.pump_motor_direction,
        PumpMotorDirectionState.FORWARD,
    )
    set_mock_value(cell.pump.pump_speed_rbv, 100)

    await assert_reading(
        cell.pump,
        {
            "pjump-pump-pump_position": {
                "value": 100,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pump-pump_forward_limit": {
                "value": LimitSwitchState.OFF,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pump-pump_backward_limit": {
                "value": LimitSwitchState.ON,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pump-pump_motor_direction": {
                "value": PumpMotorDirectionState.FORWARD,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pump-pump_speed_rbv": {
                "value": 100,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )


async def test_reading_pjumpcell_includes_read_fields_transducers(
    cell: PressureJumpCell,
):
    set_mock_value(cell.pressure_transducers[1].omron_pressure, 1001)
    set_mock_value(cell.pressure_transducers[1].omron_voltage, 2.51)
    set_mock_value(cell.pressure_transducers[1].beckhoff_pressure, 1001.1)
    set_mock_value(cell.pressure_transducers[1].beckhoff_voltage, 2.51)

    set_mock_value(cell.pressure_transducers[2].omron_pressure, 1002)
    set_mock_value(cell.pressure_transducers[2].omron_voltage, 2.52)
    set_mock_value(cell.pressure_transducers[2].beckhoff_pressure, 1002.2)
    set_mock_value(cell.pressure_transducers[2].beckhoff_voltage, 2.52)

    set_mock_value(cell.pressure_transducers[3].omron_pressure, 1003)
    set_mock_value(cell.pressure_transducers[3].omron_voltage, 2.53)
    set_mock_value(cell.pressure_transducers[3].beckhoff_pressure, 1003.3)
    set_mock_value(cell.pressure_transducers[3].beckhoff_voltage, 2.53)

    await assert_reading(
        cell.pressure_transducers[1],
        {
            "pjump-pressure_transducers-1-omron_pressure": {
                "value": 1001,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressure_transducers-1-omron_voltage": {
                "value": 2.51,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressure_transducers-1-beckhoff_pressure": {
                "value": 1001.1,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressure_transducers-1-beckhoff_voltage": {
                "value": 2.51,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )
    await assert_reading(
        cell.pressure_transducers[2],
        {
            "pjump-pressure_transducers-2-omron_pressure": {
                "value": 1002,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressure_transducers-2-omron_voltage": {
                "value": 2.52,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressure_transducers-2-beckhoff_pressure": {
                "value": 1002.2,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressure_transducers-2-beckhoff_voltage": {
                "value": 2.52,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )
    await assert_reading(
        cell.pressure_transducers[3],
        {
            "pjump-pressure_transducers-3-omron_pressure": {
                "value": 1003,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressure_transducers-3-omron_voltage": {
                "value": 2.53,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressure_transducers-3-beckhoff_pressure": {
                "value": 1003.3,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressure_transducers-3-beckhoff_voltage": {
                "value": 2.53,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )


async def test_reading_pjumpcell_includes_read_fields_controller(
    cell: PressureJumpCell,
):
    set_mock_value(cell.controller.control_gotobusy, BusyState.IDLE)
    set_mock_value(cell.controller.control_timer, TimerState.COUNTDOWN)
    set_mock_value(cell.controller.control_counter, 123)
    set_mock_value(cell.controller.control_script_status, "ABC")
    set_mock_value(cell.controller.control_routine, "CDE")
    set_mock_value(cell.controller.control_state, "EFG")
    set_mock_value(cell.controller.control_iteration, 456)

    await assert_reading(
        cell.controller,
        {
            "pjump-controller-control_gotobusy": {
                "value": BusyState.IDLE,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-controller-control_timer": {
                "value": TimerState.COUNTDOWN,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-controller-control_counter": {
                "value": 123,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-controller-control_script_status": {
                "value": "ABC",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-controller-control_routine": {
                "value": "CDE",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-controller-control_state": {
                "value": "EFG",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-controller-control_iteration": {
                "value": 456,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )


async def test_reading_pjumpcell_includes_read_fields(
    cell: PressureJumpCell,
):
    set_mock_value(cell.cell_temperature, 12.3)

    await assert_reading(
        cell.cell_temperature,
        {
            "pjump-cell_temperature": {
                "value": 12.3,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )
