from unittest.mock import ANY

import pytest
from ophyd_async.core import DeviceCollector, assert_reading, set_mock_value

from dodal.devices.pressure_jump_cell import (
    PressureJumpCell,
    PressureJumpCellBusyStatus,
    PressureJumpCellFastValveState,
    PressureJumpCellLimitSwitch,
    PressureJumpCellPumpMotorDirection,
    PressureJumpCellTimerState,
    PressureJumpCellValveState,
)


@pytest.fixture
async def pressurejumpcell() -> PressureJumpCell:
    async with DeviceCollector(mock=True):
        pjump = PressureJumpCell("DEMO-PJUMPCELL-01:")

    return pjump


async def test_reading_pjumpcell_includes_read_fields(
    pressurejumpcell: PressureJumpCell,
):
    set_mock_value(pressurejumpcell.valve1_state, PressureJumpCellValveState.CLOSED)
    set_mock_value(pressurejumpcell.valve3_state, PressureJumpCellValveState.OPEN)
    set_mock_value(
        pressurejumpcell.valve5_state, PressureJumpCellFastValveState.CLOSED_ARMED
    )
    set_mock_value(
        pressurejumpcell.valve6_state, PressureJumpCellFastValveState.OPEN_ARMED
    )
    set_mock_value(pressurejumpcell.cell_temperature, 12.3)
    set_mock_value(pressurejumpcell.pump_position, 100)
    set_mock_value(pressurejumpcell.pump_forward_limit, PressureJumpCellLimitSwitch.OFF)
    set_mock_value(pressurejumpcell.pump_backward_limit, PressureJumpCellLimitSwitch.ON)
    set_mock_value(
        pressurejumpcell.pump_motor_direction,
        PressureJumpCellPumpMotorDirection.FORWARD,
    )
    set_mock_value(pressurejumpcell.pump_speed_rbv, 100)
    set_mock_value(pressurejumpcell.pressuretransducer1_omron_pressure, 1001)
    set_mock_value(pressurejumpcell.pressuretransducer1_omron_voltage, 2.51)
    set_mock_value(pressurejumpcell.pressuretransducer1_beckhoff_pressure, 1001.1)
    set_mock_value(pressurejumpcell.pressuretransducer1_beckhoff_voltage, 2.51)
    set_mock_value(pressurejumpcell.pressuretransducer2_omron_pressure, 1002)
    set_mock_value(pressurejumpcell.pressuretransducer2_omron_voltage, 2.52)
    set_mock_value(pressurejumpcell.pressuretransducer2_beckhoff_pressure, 1002.2)
    set_mock_value(pressurejumpcell.pressuretransducer2_beckhoff_voltage, 2.52)
    set_mock_value(pressurejumpcell.pressuretransducer3_omron_pressure, 1003)
    set_mock_value(pressurejumpcell.pressuretransducer3_omron_voltage, 2.53)
    set_mock_value(pressurejumpcell.pressuretransducer3_beckhoff_pressure, 1003.3)
    set_mock_value(pressurejumpcell.pressuretransducer3_beckhoff_voltage, 2.53)
    set_mock_value(pressurejumpcell.control_gotobusy, PressureJumpCellBusyStatus.IDLE)
    set_mock_value(pressurejumpcell.control_timer, PressureJumpCellTimerState.COUNTDOWN)
    set_mock_value(pressurejumpcell.control_counter, 123)
    set_mock_value(pressurejumpcell.control_script_status, "ABC")
    set_mock_value(pressurejumpcell.control_routine, "CDE")
    set_mock_value(pressurejumpcell.control_state, "EFG")
    set_mock_value(pressurejumpcell.control_iteration, 456)

    await assert_reading(
        pressurejumpcell,
        {
            "pjump-valve1_state": {
                "value": PressureJumpCellValveState.CLOSED,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-valve3_state": {
                "value": PressureJumpCellValveState.OPEN,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-valve5_state": {
                "value": PressureJumpCellFastValveState.CLOSED_ARMED,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-valve6_state": {
                "value": PressureJumpCellFastValveState.OPEN_ARMED,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-cell_temperature": {
                "value": 12.3,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pump_position": {
                "value": 100,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pump_forward_limit": {
                "value": PressureJumpCellLimitSwitch.OFF,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pump_backward_limit": {
                "value": PressureJumpCellLimitSwitch.ON,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pump_motor_direction": {
                "value": PressureJumpCellPumpMotorDirection.FORWARD,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pump_speed_rbv": {
                "value": 100,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressuretransducer1_omron_pressure": {
                "value": 1001,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressuretransducer1_omron_voltage": {
                "value": 2.51,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressuretransducer1_beckhoff_pressure": {
                "value": 1001.1,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressuretransducer1_beckhoff_voltage": {
                "value": 2.51,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressuretransducer2_omron_pressure": {
                "value": 1002,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressuretransducer2_omron_voltage": {
                "value": 2.52,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressuretransducer2_beckhoff_pressure": {
                "value": 1002.2,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressuretransducer2_beckhoff_voltage": {
                "value": 2.52,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressuretransducer3_omron_pressure": {
                "value": 1003,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressuretransducer3_omron_voltage": {
                "value": 2.53,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressuretransducer3_beckhoff_pressure": {
                "value": 1003.3,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pressuretransducer3_beckhoff_voltage": {
                "value": 2.53,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-control_gotobusy": {
                "value": PressureJumpCellBusyStatus.IDLE,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-control_timer": {
                "value": PressureJumpCellTimerState.COUNTDOWN,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-control_counter": {
                "value": 123,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-control_script_status": {
                "value": "ABC",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-control_routine": {
                "value": "CDE",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-control_state": {
                "value": "EFG",
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-control_iteration": {
                "value": 456,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )
