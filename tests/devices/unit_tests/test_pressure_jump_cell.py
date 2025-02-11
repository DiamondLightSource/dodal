import asyncio
from unittest.mock import ANY

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, set_mock_value

from dodal.devices.pressure_jump_cell import (
    FastValveControlRequest,
    FastValveState,
    PressureJumpCell,
    PumpMotorDirectionState,
    ValveControlRequest,
    ValveOpenSeqRequest,
    ValveState,
)


@pytest.fixture
async def cell() -> PressureJumpCell:
    async with init_devices(mock=True):
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


async def test_reading_pjumpcell_includes_config_fields_valves(
    cell: PressureJumpCell,
):
    set_mock_value(
        cell.all_valves_control.valve_control[1].close, ValveControlRequest.CLOSE
    )
    set_mock_value(
        cell.all_valves_control.valve_control[3].close, ValveControlRequest.OPEN
    )
    set_mock_value(
        cell.all_valves_control.valve_control[1].open,
        ValveOpenSeqRequest.INACTIVE.value,
    )
    set_mock_value(
        cell.all_valves_control.valve_control[3].open,
        ValveOpenSeqRequest.OPEN_SEQ.value,
    )

    set_mock_value(
        cell.all_valves_control.fast_valve_control[5].close,
        FastValveControlRequest.DISARM,
    )
    set_mock_value(
        cell.all_valves_control.fast_valve_control[6].close, FastValveControlRequest.ARM
    )
    set_mock_value(
        cell.all_valves_control.fast_valve_control[5].open,
        ValveOpenSeqRequest.INACTIVE.value,
    )
    set_mock_value(
        cell.all_valves_control.fast_valve_control[6].open,
        ValveOpenSeqRequest.OPEN_SEQ.value,
    )

    await assert_reading(
        cell.all_valves_control.valve_control[1],
        {
            "pjump-all_valves_control-valve_control-1-open": {
                "value": int(ValveOpenSeqRequest.INACTIVE.value),
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-all_valves_control-valve_control-1-close": {
                "value": ValveControlRequest.CLOSE,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )


async def test_pjumpcell_set_valve_sets_valve_fields(
    cell: PressureJumpCell,
):
    # Set some initial values
    set_mock_value(
        cell.all_valves_control.valve_control[1].close, ValveControlRequest.RESET
    )
    set_mock_value(
        cell.all_valves_control.valve_control[1].open,
        ValveOpenSeqRequest.INACTIVE.value,
    )

    set_mock_value(
        cell.all_valves_control.fast_valve_control[6].close,
        FastValveControlRequest.RESET,
    )

    set_mock_value(
        cell.all_valves_control.fast_valve_control[6].open,
        ValveOpenSeqRequest.INACTIVE.value,
    )

    # Set new values

    await cell.all_valves_control.set_valve(1, ValveControlRequest.CLOSE)
    await cell.all_valves_control.set_valve(6, FastValveControlRequest.ARM)

    await asyncio.gather(
        cell.all_valves_control.set_valve(1, ValveControlRequest.OPEN),
        cell.all_valves_control.set_valve(6, FastValveControlRequest.OPEN),
        # Check valves requested to open are set to OPEN_SEQ on initially calling
        # set_valve()
        assert_reading(
            cell.all_valves_control.valve_control[1],
            {
                "pjump-all_valves_control-valve_control-1-open": {
                    "value": int(ValveOpenSeqRequest.OPEN_SEQ.value),
                    "timestamp": ANY,
                    "alarm_severity": 0,
                },
                "pjump-all_valves_control-valve_control-1-close": {
                    "value": ANY,
                    "timestamp": ANY,
                    "alarm_severity": 0,
                },
            },
        ),
        assert_reading(
            cell.all_valves_control.fast_valve_control[6],
            {
                "pjump-all_valves_control-fast_valve_control-6-open": {
                    "value": int(ValveOpenSeqRequest.OPEN_SEQ.value),
                    "timestamp": ANY,
                    "alarm_severity": 0,
                },
                "pjump-all_valves_control-fast_valve_control-6-close": {
                    "value": ANY,
                    "timestamp": ANY,
                    "alarm_severity": 0,
                },
            },
        ),
    )

    # Check slow valves have been set to the new value and valves requested to open are
    # set to INACTIVE after set_valve() completes
    await assert_reading(
        cell.all_valves_control.valve_control[1],
        {
            "pjump-all_valves_control-valve_control-1-open": {
                "value": int(ValveOpenSeqRequest.INACTIVE.value),
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-all_valves_control-valve_control-1-close": {
                "value": ValveControlRequest.CLOSE,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )

    # Check fast valves have been set to the new value and valves requested to open are
    # set to INACTIVE after set_valve() completes
    await assert_reading(
        cell.all_valves_control.fast_valve_control[6],
        {
            "pjump-all_valves_control-fast_valve_control-6-close": {
                "value": FastValveControlRequest.ARM,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-all_valves_control-fast_valve_control-6-open": {
                "value": int(ValveOpenSeqRequest.INACTIVE.value),
                "timestamp": ANY,
                "alarm_severity": 0,
            },
        },
    )


async def test_reading_pjumpcell_includes_read_fields_pump(
    cell: PressureJumpCell,
):
    set_mock_value(cell.pump.pump_position, 100)
    set_mock_value(
        cell.pump.pump_motor_direction,
        PumpMotorDirectionState.FORWARD,
    )
    set_mock_value(cell.pump.pump_speed, 100)

    await assert_reading(
        cell.pump,
        {
            "pjump-pump-pump_position": {
                "value": 100,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pump-pump_motor_direction": {
                "value": PumpMotorDirectionState.FORWARD,
                "timestamp": ANY,
                "alarm_severity": 0,
            },
            "pjump-pump-pump_speed": {
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
    set_mock_value(cell.pressure_transducers[1].slow_beckhoff_voltage_readout, 2.51)

    set_mock_value(cell.pressure_transducers[2].omron_pressure, 1002)
    set_mock_value(cell.pressure_transducers[2].omron_voltage, 2.52)
    set_mock_value(cell.pressure_transducers[2].beckhoff_pressure, 1002.2)
    set_mock_value(cell.pressure_transducers[2].slow_beckhoff_voltage_readout, 2.52)

    set_mock_value(cell.pressure_transducers[3].omron_pressure, 1003)
    set_mock_value(cell.pressure_transducers[3].omron_voltage, 2.53)
    set_mock_value(cell.pressure_transducers[3].beckhoff_pressure, 1003.3)
    set_mock_value(cell.pressure_transducers[3].slow_beckhoff_voltage_readout, 2.53)

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
            "pjump-pressure_transducers-1-slow_beckhoff_voltage_readout": {
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
            "pjump-pressure_transducers-2-slow_beckhoff_voltage_readout": {
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
            "pjump-pressure_transducers-3-slow_beckhoff_voltage_readout": {
                "value": 2.53,
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
