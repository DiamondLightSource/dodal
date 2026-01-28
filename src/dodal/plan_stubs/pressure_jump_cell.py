import bluesky.plan_stubs as bps

from dodal.devices.pressure_jump_cell import PressureJumpCell


def set_pressure_jump(
    pressure_cell: PressureJumpCell, pressure_from: int, pressure_to: int
):
    """Sets the desired pressures for a jump waiting for the device to complete the
    operation."""
    yield from bps.mv(
        pressure_cell.control.from_pressure,
        pressure_from,
        pressure_cell.control.to_pressure,
        pressure_to,
    )
    yield from bps.trigger(pressure_cell.control.do_jump, wait=True)
