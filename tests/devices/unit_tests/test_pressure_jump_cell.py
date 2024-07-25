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


async def test_reading_pjumpcell_includes_read_fields_valves(
    pressurejumpcell: PressureJumpCell,
):
    set_mock_value(
        pressurejumpcell.valves.valve1_state, PressureJumpCellValveState.CLOSED
    )
    set_mock_value(
        pressurejumpcell.valves.valve3_state, PressureJumpCellValveState.OPEN
    )
    set_mock_value(
        pressurejumpcell.valves.valve5_state,
        PressureJumpCellFastValveState.CLOSED_ARMED,
    )
    set_mock_value(
        pressurejumpcell.valves.valve6_state, PressureJumpCellFastValveState.OPEN_ARMED
    )

    await assert_reading(
        pressurejumpcell.valves,
        {
            "pjump-valves-valve1_state": {
                "value": PressureJumpCellValveState.CLOSED,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-valves-valve3_state": {
                "value": PressureJumpCellValveState.OPEN,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-valves-valve5_state": {
                "value": PressureJumpCellFastValveState.CLOSED_ARMED,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-valves-valve6_state": {
                "value": PressureJumpCellFastValveState.OPEN_ARMED,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )


async def test_reading_pjumpcell_includes_read_fields_pump(
    pressurejumpcell: PressureJumpCell,
):
    set_mock_value(pressurejumpcell.pump.pump_position, 100)
    set_mock_value(
        pressurejumpcell.pump.pump_forward_limit, PressureJumpCellLimitSwitch.OFF
    )
    set_mock_value(
        pressurejumpcell.pump.pump_backward_limit, PressureJumpCellLimitSwitch.ON
    )
    set_mock_value(
        pressurejumpcell.pump.pump_motor_direction,
        PressureJumpCellPumpMotorDirection.FORWARD,
    )
    set_mock_value(pressurejumpcell.pump.pump_speed_rbv, 100)

    await assert_reading(
        pressurejumpcell.pump,
        {
            "pjump-pump-pump_position": {
                "value": 100,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pump-pump_forward_limit": {
                "value": PressureJumpCellLimitSwitch.OFF,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pump-pump_backward_limit": {
                "value": PressureJumpCellLimitSwitch.ON,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pump-pump_motor_direction": {
                "value": PressureJumpCellPumpMotorDirection.FORWARD,
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
    pressurejumpcell: PressureJumpCell,
):
    set_mock_value(
        pressurejumpcell.transducers.pressuretransducer1_omron_pressure, 1001
    )
    set_mock_value(pressurejumpcell.transducers.pressuretransducer1_omron_voltage, 2.51)
    set_mock_value(
        pressurejumpcell.transducers.pressuretransducer1_beckhoff_pressure, 1001.1
    )
    set_mock_value(
        pressurejumpcell.transducers.pressuretransducer1_beckhoff_voltage, 2.51
    )
    set_mock_value(
        pressurejumpcell.transducers.pressuretransducer2_omron_pressure, 1002
    )
    set_mock_value(pressurejumpcell.transducers.pressuretransducer2_omron_voltage, 2.52)
    set_mock_value(
        pressurejumpcell.transducers.pressuretransducer2_beckhoff_pressure, 1002.2
    )
    set_mock_value(
        pressurejumpcell.transducers.pressuretransducer2_beckhoff_voltage, 2.52
    )
    set_mock_value(
        pressurejumpcell.transducers.pressuretransducer3_omron_pressure, 1003
    )
    set_mock_value(pressurejumpcell.transducers.pressuretransducer3_omron_voltage, 2.53)
    set_mock_value(
        pressurejumpcell.transducers.pressuretransducer3_beckhoff_pressure, 1003.3
    )
    set_mock_value(
        pressurejumpcell.transducers.pressuretransducer3_beckhoff_voltage, 2.53
    )

    await assert_reading(
        pressurejumpcell.transducers,
        {
            "pjump-transducers-pressuretransducer1_omron_pressure": {
                "value": 1001,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-transducers-pressuretransducer1_omron_voltage": {
                "value": 2.51,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-transducers-pressuretransducer1_beckhoff_pressure": {
                "value": 1001.1,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-transducers-pressuretransducer1_beckhoff_voltage": {
                "value": 2.51,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-transducers-pressuretransducer2_omron_pressure": {
                "value": 1002,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-transducers-pressuretransducer2_omron_voltage": {
                "value": 2.52,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-transducers-pressuretransducer2_beckhoff_pressure": {
                "value": 1002.2,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-transducers-pressuretransducer2_beckhoff_voltage": {
                "value": 2.52,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-transducers-pressuretransducer3_omron_pressure": {
                "value": 1003,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-transducers-pressuretransducer3_omron_voltage": {
                "value": 2.53,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-transducers-pressuretransducer3_beckhoff_pressure": {
                "value": 1003.3,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-transducers-pressuretransducer3_beckhoff_voltage": {
                "value": 2.53,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )


async def test_reading_pjumpcell_includes_read_fields_controller(
    pressurejumpcell: PressureJumpCell,
):
    set_mock_value(
        pressurejumpcell.controller.control_gotobusy, PressureJumpCellBusyStatus.IDLE
    )
    set_mock_value(
        pressurejumpcell.controller.control_timer, PressureJumpCellTimerState.COUNTDOWN
    )
    set_mock_value(pressurejumpcell.controller.control_counter, 123)
    set_mock_value(pressurejumpcell.controller.control_script_status, "ABC")
    set_mock_value(pressurejumpcell.controller.control_routine, "CDE")
    set_mock_value(pressurejumpcell.controller.control_state, "EFG")
    set_mock_value(pressurejumpcell.controller.control_iteration, 456)

    await assert_reading(
        pressurejumpcell.controller,
        {
            "pjump-controller-control_gotobusy": {
                "value": PressureJumpCellBusyStatus.IDLE,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-controller-control_timer": {
                "value": PressureJumpCellTimerState.COUNTDOWN,
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
    pressurejumpcell: PressureJumpCell,
):
    set_mock_value(pressurejumpcell.cell_temperature, 12.3)

    await assert_reading(
        pressurejumpcell,
        {
            "pjump-cell_temperature": {
                "value": 12.3,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )
