import bluesky.plan_stubs as bps

from dodal.devices.pressure_jump_cell import PressureJumpCell, PressureJumpParameters


def set_pressure(pressure_cell: PressureJumpCell, pressure: int):
    """
    Sets the desired pressure waiting for the device to complete the operation.
    """
    yield from bps.mv(pressure_cell.control, pressure)


def set_pressure_jump(
    pressure_cell: PressureJumpCell, pressure_from: int, pressure_to: int
):
    """
    Sets the desired pressures for a jump waiting for the device to complete the operation.
    """
    jump_params = PressureJumpParameters(pressure_from, pressure_to)
    yield from bps.mv(pressure_cell.control, jump_params)


from dodal.devices.pressure_jump_cell import (
    FastValveControlRequest,
    FastValveState,
    PressureJumpCell,
    ValveControlRequest,
    ValveState,
)


def prepare_fast_pressure_jump(
    pressure_cell: PressureJumpCell, pressure_from: int, pressure_to: int
):
    """
    Sets up the pressures for a fast pressure jump and arms a fast valve ready.

    It is expected that the valves be in the following states: V1 is closed and V3, V5,
    and V6 are open.
    """

    jump_direction_up: bool = pressure_to > pressure_from

    # Check inital condition
    v1 = yield from bps.rd(pressure_cell.all_valves_control.valve_states[1])
    v3 = yield from bps.rd(pressure_cell.all_valves_control.valve_states[3])
    v5 = yield from bps.rd(pressure_cell.all_valves_control.fast_valve_states[5])
    v6 = yield from bps.rd(pressure_cell.all_valves_control.fast_valve_states[6])

    if not (
        v1 == ValveState.CLOSED
        and v3 == ValveState.OPEN
        and v5 == FastValveState.OPEN
        and v6 == FastValveState.OPEN
    ):
        raise Exception(
            "Exception valves not in the expected states - check V1 is closed and V3, V5 and V6 are open."
        )

    # Bring the cell upto the jump from pressure
    yield from bps.mv(pressure_cell.control, pressure_from)
    yield from bps.mv(
        pressure_cell.all_valves_control.valve_control[5],
        ValveControlRequest.CLOSE,
        pressure_cell.all_valves_control.valve_control[6],
        ValveControlRequest.CLOSE
    )

    # Bring the reservoir section upto the jump to pressure
    yield from bps.mv(pressure_cell.control, pressure_to)
    yield from bps.mv(
        pressure_cell.all_valves_control.valve_control[3], ValveControlRequest.CLOSE
    )

    # Prepare for AD capture
    if jump_direction_up:
        yield from bps.mv(
            pressure_cell.all_valves_control.valve_control[5],
            FastValveControlRequest.ARM
        )
    else:
        yield from bps.mv(
            pressure_cell.all_valves_control.valve_control[6],
            FastValveControlRequest.ARM
        )
