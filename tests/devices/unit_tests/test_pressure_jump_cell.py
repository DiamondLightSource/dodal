import asyncio

import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading, set_mock_value

from dodal.devices.pressure_jump_cell import (
    OPENSEQ_PULSE_LENGTH,
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
            "pjump-all_valves_control-valve_states-1": partial_reading(
                ValveState.CLOSED
            ),
            "pjump-all_valves_control-valve_states-3": partial_reading(ValveState.OPEN),
            "pjump-all_valves_control-fast_valve_states-5": partial_reading(
                FastValveState.CLOSED_ARMED
            ),
            "pjump-all_valves_control-fast_valve_states-6": partial_reading(
                FastValveState.OPEN_ARMED
            ),
        },
    )


async def test_reading_pjumpcell_includes_config_fields_valves(
    cell: PressureJumpCell,
):
    set_mock_value(
        cell.all_valves_control.valve_control[1].control, ValveControlRequest.CLOSE
    )
    set_mock_value(
        cell.all_valves_control.valve_control[3].control, ValveControlRequest.OPEN
    )
    set_mock_value(
        cell.all_valves_control.valve_control[1].open,
        ValveOpenSeqRequest.INACTIVE,
    )
    set_mock_value(
        cell.all_valves_control.valve_control[3].open,
        ValveOpenSeqRequest.OPEN_SEQ,
    )

    set_mock_value(
        cell.all_valves_control.valve_control[5].control,
        FastValveControlRequest.DISARM,
    )
    set_mock_value(
        cell.all_valves_control.valve_control[6].control, FastValveControlRequest.ARM
    )
    set_mock_value(
        cell.all_valves_control.valve_control[5].open,
        ValveOpenSeqRequest.INACTIVE,
    )
    set_mock_value(
        cell.all_valves_control.valve_control[6].open,
        ValveOpenSeqRequest.OPEN_SEQ,
    )

    await assert_reading(
        cell.all_valves_control.valve_control[1],
        {
            "pjump-all_valves_control-valve_control-1-open": partial_reading(
                int(ValveOpenSeqRequest.INACTIVE.value)
            ),
            "pjump-all_valves_control-valve_control-1-control": partial_reading(
                ValveControlRequest.CLOSE
            ),
        },
    )


async def test_pjumpcell_set_valve_sets_valve_fields(
    cell: PressureJumpCell,
):
    # Set some initial values
    set_mock_value(
        cell.all_valves_control.valve_control[1].control, ValveControlRequest.RESET
    )
    set_mock_value(
        cell.all_valves_control.valve_control[1].open,
        ValveOpenSeqRequest.INACTIVE,
    )

    set_mock_value(
        cell.all_valves_control.valve_control[6].control,
        FastValveControlRequest.RESET,
    )

    set_mock_value(
        cell.all_valves_control.valve_control[6].open,
        ValveOpenSeqRequest.INACTIVE,
    )

    # Set new values
    await cell.all_valves_control.valve_control[1].set(ValveControlRequest.CLOSE)
    await cell.all_valves_control.fast_valve_control[6].set(FastValveControlRequest.ARM)

    opening_status = asyncio.gather(
        cell.all_valves_control.valve_control[1].set(ValveControlRequest.OPEN),
        cell.all_valves_control.fast_valve_control[6].set(FastValveControlRequest.OPEN),
    )

    # During openseq pulse
    await asyncio.sleep(OPENSEQ_PULSE_LENGTH / 2)

    # Check valves requested to open are set to OPEN_SEQ after calling set_valve()
    await assert_reading(
        cell.all_valves_control.valve_control[1],
        {
            "pjump-all_valves_control-valve_control-1-open": partial_reading(
                int(ValveOpenSeqRequest.OPEN_SEQ.value)
            ),
            "pjump-all_valves_control-valve_control-1-control": partial_reading(
                ValveControlRequest.CLOSE
            ),
        },
    )
    await assert_reading(
        cell.all_valves_control.valve_control[6],
        {
            "pjump-all_valves_control-valve_control-6-open": partial_reading(
                int(ValveOpenSeqRequest.OPEN_SEQ.value)
            ),
            "pjump-all_valves_control-valve_control-6-control": partial_reading(
                FastValveControlRequest.ARM
            ),
        },
    )
    # After openseq pulse
    await opening_status

    # Check slow valves have been set to the new value and valves requested to open are
    # set to INACTIVE after set_valve() completes
    await assert_reading(
        cell.all_valves_control.valve_control[1],
        {
            "pjump-all_valves_control-valve_control-1-open": partial_reading(
                int(ValveOpenSeqRequest.INACTIVE.value)
            ),
            "pjump-all_valves_control-valve_control-1-control": partial_reading(
                ValveControlRequest.CLOSE
            ),
        },
    )

    # Check fast valves have been set to the new value and valves requested to open are
    # set to INACTIVE after set_valve() completes
    await assert_reading(
        cell.all_valves_control.valve_control[6],
        {
            "pjump-all_valves_control-valve_control-6-open": partial_reading(
                int(ValveOpenSeqRequest.INACTIVE.value)
            ),
            "pjump-all_valves_control-valve_control-6-control": partial_reading(
                FastValveControlRequest.ARM
            ),
        },
    )


@pytest.mark.parametrize(
    "valve_request,expected",
    [
        (ValveControlRequest.CLOSE, FastValveControlRequest.CLOSE),
        (ValveControlRequest.RESET, FastValveControlRequest.RESET),
        (ValveControlRequest.OPEN, FastValveControlRequest.ARM),  # Unchanged as openseq
    ],
)
async def test_pjumpcell_set_valve_sets_control_request_for_all_valve_types(
    cell: PressureJumpCell,
    valve_request: ValveControlRequest,
    expected: FastValveControlRequest,
):
    # Set some initial values
    set_mock_value(
        cell.all_valves_control.valve_control[5].control,
        FastValveControlRequest.ARM.value,
    )

    set_mock_value(
        cell.all_valves_control.valve_control[5].open,
        ValveOpenSeqRequest.INACTIVE,
    )

    # Set new values
    await asyncio.gather(
        cell.all_valves_control.valve_control[5].set(valve_request),
    )

    # Check the fast valve value has been set to the equivalent FastValveControlRequest
    # value
    await assert_reading(
        cell.all_valves_control.valve_control[5],
        {
            "pjump-all_valves_control-valve_control-5-open": partial_reading(
                int(ValveOpenSeqRequest.INACTIVE.value)
            ),
            "pjump-all_valves_control-valve_control-5-control": partial_reading(
                expected
            ),
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
            "pjump-pump-pump_position": partial_reading(100),
            "pjump-pump-pump_motor_direction": partial_reading(
                PumpMotorDirectionState.FORWARD
            ),
            "pjump-pump-pump_speed": partial_reading(100),
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
            "pjump-pressure_transducers-1-omron_pressure": partial_reading(1001),
            "pjump-pressure_transducers-1-omron_voltage": partial_reading(2.51),
            "pjump-pressure_transducers-1-beckhoff_pressure": partial_reading(1001.1),
            "pjump-pressure_transducers-1-slow_beckhoff_voltage_readout": partial_reading(
                2.51
            ),
        },
    )
    await assert_reading(
        cell.pressure_transducers[2],
        {
            "pjump-pressure_transducers-2-omron_pressure": partial_reading(1002),
            "pjump-pressure_transducers-2-omron_voltage": partial_reading(2.52),
            "pjump-pressure_transducers-2-beckhoff_pressure": partial_reading(1002.2),
            "pjump-pressure_transducers-2-slow_beckhoff_voltage_readout": partial_reading(
                2.52
            ),
        },
    )
    await assert_reading(
        cell.pressure_transducers[3],
        {
            "pjump-pressure_transducers-3-omron_pressure": partial_reading(1003),
            "pjump-pressure_transducers-3-omron_voltage": partial_reading(2.53),
            "pjump-pressure_transducers-3-beckhoff_pressure": partial_reading(1003.3),
            "pjump-pressure_transducers-3-slow_beckhoff_voltage_readout": partial_reading(
                2.53
            ),
        },
    )


async def test_reading_pjumpcell_includes_read_fields(
    cell: PressureJumpCell,
):
    set_mock_value(cell.cell_temperature, 12.3)

    await assert_reading(
        cell.cell_temperature,
        {
            "pjump-cell_temperature": partial_reading(12.3),
        },
    )


async def test_setting_all_pressure_cell_valves(
    cell: PressureJumpCell,
):
    # Set some initial values
    set_mock_value(
        cell.all_valves_control.valve_control[1].control, ValveControlRequest.RESET
    )
    set_mock_value(
        cell.all_valves_control.valve_control[1].open,
        ValveOpenSeqRequest.INACTIVE,
    )

    set_mock_value(
        cell.all_valves_control.valve_control[3].control, ValveControlRequest.RESET
    )
    set_mock_value(
        cell.all_valves_control.valve_control[3].open,
        ValveOpenSeqRequest.INACTIVE,
    )

    set_mock_value(
        cell.all_valves_control.valve_control[5].control,
        FastValveControlRequest.RESET,
    )

    set_mock_value(
        cell.all_valves_control.valve_control[5].open,
        ValveOpenSeqRequest.INACTIVE,
    )

    set_mock_value(
        cell.all_valves_control.valve_control[6].control,
        FastValveControlRequest.RESET,
    )

    set_mock_value(
        cell.all_valves_control.valve_control[6].open,
        ValveOpenSeqRequest.INACTIVE,
    )

    # Set new values
    for valve in cell.all_valves_control.valve_control.values():
        await valve.set(ValveControlRequest.CLOSE)

    # Check valves have been set to the new values
    await assert_reading(
        cell.all_valves_control.valve_control[1],
        {
            "pjump-all_valves_control-valve_control-1-open": partial_reading(
                int(ValveOpenSeqRequest.INACTIVE.value)
            ),
            "pjump-all_valves_control-valve_control-1-control": partial_reading(
                ValveControlRequest.CLOSE,
            ),
        },
    )

    await assert_reading(
        cell.all_valves_control.valve_control[3],
        {
            "pjump-all_valves_control-valve_control-3-open": partial_reading(
                int(ValveOpenSeqRequest.INACTIVE.value)
            ),
            "pjump-all_valves_control-valve_control-3-control": partial_reading(
                ValveControlRequest.CLOSE
            ),
        },
    )

    await assert_reading(
        cell.all_valves_control.valve_control[5],
        {
            "pjump-all_valves_control-valve_control-5-open": partial_reading(
                int(ValveOpenSeqRequest.INACTIVE.value),
            ),
            "pjump-all_valves_control-valve_control-5-control": partial_reading(
                FastValveControlRequest.CLOSE,
            ),
        },
    )

    await assert_reading(
        cell.all_valves_control.valve_control[6],
        {
            "pjump-all_valves_control-valve_control-6-open": partial_reading(
                int(ValveOpenSeqRequest.INACTIVE.value),
            ),
            "pjump-all_valves_control-valve_control-6-control": partial_reading(
                FastValveControlRequest.CLOSE,
            ),
        },
    )
