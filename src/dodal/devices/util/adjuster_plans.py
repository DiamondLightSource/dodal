"""
All the methods in this module return a bluesky plan generator that adjusts a value
according to some criteria either via feedback, preset positions, lookup tables etc.
"""

from typing import Callable, Generator

from bluesky import plan_stubs as bps
from bluesky.run_engine import Msg
from ophyd.epics_motor import EpicsMotor
from ophyd_async.epics.motion import Motor

from dodal.log import LOGGER


def lookup_table_adjuster(
    lookup_table: Callable[[float], float], output_device: EpicsMotor | Motor, input
):
    """Returns a callable that adjusts a value according to a lookup table"""

    def adjust(group=None) -> Generator[Msg, None, None]:
        setpoint = lookup_table(input)
        LOGGER.info(f"lookup_table_adjuster setting {output_device.name} to {setpoint}")
        yield from bps.abs_set(output_device, setpoint, group=group)

    return adjust
