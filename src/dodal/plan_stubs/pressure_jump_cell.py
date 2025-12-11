import bluesky.plan_stubs as bps

from dodal.devices.pressure_jump_cell import PressureJumpCell, PressureJumpParameters


def test():
    yield from bps.wait()


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
