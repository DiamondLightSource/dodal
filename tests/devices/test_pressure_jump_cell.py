import asyncio
from unittest.mock import ANY

import pytest
from ophyd_async.core import DeviceMock, init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

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


@pytest.fixture
async def cell_with_no_mocks() -> PressureJumpCell:
    async with init_devices(mock=True):
        pjump = PressureJumpCell("DEMO-PJUMPCELL-02:")
        await pjump.connect(mock=DeviceMock())

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


async def test_reading_pjumpcell_includes_fields_control(
    cell: PressureJumpCell,
):
    set_mock_value(cell.control.go, False)
    set_mock_value(cell.control._stop, False)
    set_mock_value(cell.control.busy, False)
    set_mock_value(cell.control.target_pressure, 0)
    set_mock_value(cell.control.timeout, 0.0)
    set_mock_value(cell.control.result, "SP_SUCCESS")

    await assert_reading(
        cell.control,
        {
            "pjump-control-busy": partial_reading(False),
            "pjump-control-go": partial_reading(False),
            "pjump-control-result": partial_reading("SP_SUCCESS"),
            "pjump-control-target_pressure": partial_reading(0),
            "pjump-control-timeout": partial_reading(0.0),
            "pjump-control-_stop": partial_reading(False),
            "pjump-control-from_pressure": partial_reading(ANY),
            "pjump-control-to_pressure": partial_reading(ANY),
            "pjump-control-do_jump-set_jump": partial_reading(ANY),
        },
    )


async def test_reading_pjumpcell_includes_fields_control_jump(
    cell: PressureJumpCell,
):
    set_mock_value(cell.control._stop, False)
    set_mock_value(cell.control.busy, False)
    set_mock_value(cell.control.from_pressure, 0)
    set_mock_value(cell.control.to_pressure, 0)
    set_mock_value(cell.control.timeout, 0.0)
    set_mock_value(cell.control.result, "SP_SUCCESS")
    set_mock_value(cell.control.do_jump.set_jump, False)

    await assert_reading(
        cell.control,
        {
            "pjump-control-busy": partial_reading(False),
            "pjump-control-go": partial_reading(False),
            "pjump-control-result": partial_reading("SP_SUCCESS"),
            "pjump-control-target_pressure": partial_reading(ANY),
            "pjump-control-timeout": partial_reading(0.0),
            "pjump-control-_stop": partial_reading(False),
            "pjump-control-from_pressure": partial_reading(0.0),
            "pjump-control-to_pressure": partial_reading(0.0),
            "pjump-control-do_jump-set_jump": partial_reading(False),
        },
    )


async def test_pjumpcell_toplevel_pressure_control(
    cell: PressureJumpCell,
):
    target_pressure = 250
    set_mock_value(cell.control.go, False)
    set_mock_value(cell.control._stop, False)
    set_mock_value(cell.control.busy, False)
    set_mock_value(cell.control.target_pressure, 0)
    set_mock_value(cell.control.timeout, 1)
    set_mock_value(cell.control.result, "SP_SUCCESS")

    await cell.control.set(target_pressure)

    await assert_reading(
        cell.control,
        {
            "pjump-control-busy": partial_reading(False),
            "pjump-control-go": partial_reading(True),
            "pjump-control-result": partial_reading("SP_SUCCESS"),
            "pjump-control-target_pressure": partial_reading(target_pressure),
            "pjump-control-timeout": partial_reading(ANY),
            "pjump-control-_stop": partial_reading(False),
            "pjump-control-from_pressure": partial_reading(ANY),
            "pjump-control-to_pressure": partial_reading(ANY),
            "pjump-control-do_jump-set_jump": partial_reading(ANY),
        },
    )


async def test_pjumpcell_toplevel_pressure_jump_control(
    cell: PressureJumpCell,
):
    target_pressure_from = 500
    target_pressure_to = 1000
    set_mock_value(cell.control.go, False)
    set_mock_value(cell.control._stop, False)
    set_mock_value(cell.control.busy, False)
    set_mock_value(cell.control.target_pressure, 0)
    set_mock_value(cell.control.from_pressure, 0)
    set_mock_value(cell.control.to_pressure, 0)
    set_mock_value(cell.control.timeout, 1)
    set_mock_value(cell.control.result, "SP_SUCCESS")
    set_mock_value(cell.control.do_jump.set_jump, False)

    await cell.control.from_pressure.set(target_pressure_from)
    await cell.control.to_pressure.set(target_pressure_to)
    await cell.control.do_jump.trigger()

    await assert_reading(
        cell.control,
        {
            "pjump-control-busy": partial_reading(False),
            "pjump-control-do_jump-set_jump": partial_reading(True),
            "pjump-control-result": partial_reading("SP_SUCCESS"),
            "pjump-control-timeout": partial_reading(ANY),
            "pjump-control-_stop": partial_reading(False),
            "pjump-control-from_pressure": partial_reading(target_pressure_from),
            "pjump-control-to_pressure": partial_reading(target_pressure_to),
            "pjump-control-go": partial_reading(False),
            "pjump-control-target_pressure": partial_reading(ANY),
        },
    )


async def test_pjumpcell_toplevel_pressure_control_waits_on_busy(
    cell_with_no_mocks: PressureJumpCell,
):
    target_pressure = 500

    set_mock_value(cell_with_no_mocks.control.go, False)
    set_mock_value(cell_with_no_mocks.control._stop, False)
    set_mock_value(cell_with_no_mocks.control.busy, True)
    set_mock_value(cell_with_no_mocks.control.target_pressure, 0)
    set_mock_value(cell_with_no_mocks.control.timeout, 1)
    set_mock_value(cell_with_no_mocks.control.result, "SP_SUCCESS")

    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.05):
            await cell_with_no_mocks.control.set(target_pressure)


async def test_pjumpcell_toplevel_pressure_control_stops(
    cell: PressureJumpCell,
):
    set_mock_value(cell.control.go, False)
    set_mock_value(cell.control._stop, False)
    set_mock_value(cell.control.busy, True)
    set_mock_value(cell.control.target_pressure, 0)
    set_mock_value(cell.control.timeout, 1)
    set_mock_value(cell.control.result, "SP_SUCCESS")

    await cell.control.stop()

    await assert_reading(
        cell.control,
        {
            "pjump-control-busy": partial_reading(ANY),
            "pjump-control-result": partial_reading(ANY),
            "pjump-control-timeout": partial_reading(ANY),
            "pjump-control-_stop": partial_reading(True),
            "pjump-control-from_pressure": partial_reading(ANY),
            "pjump-control-to_pressure": partial_reading(ANY),
            "pjump-control-go": partial_reading(ANY),
            "pjump-control-target_pressure": partial_reading(ANY),
            "pjump-control-do_jump-set_jump": partial_reading(ANY),
        },
    )
