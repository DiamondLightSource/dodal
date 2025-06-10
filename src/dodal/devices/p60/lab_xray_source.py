from enum import Enum

from ophyd_async.core import (
    StandardReadable,
    soft_signal_rw,
)
from ophyd_async.core import StandardReadableFormat as Format

# Must conform src/dodal/devices/electron_analyser/abstract/base_driver_io.py


class LabXraySource(Enum):
    AlKa = 1486.6
    MgKa = 1253.6


class LabXraySourceReadable(StandardReadable):
    """Simple device to get the laboratory x-ray tube energy reading"""

    def __init__(self, xraysource: Enum, name: str) -> None:
        with self.add_children_as_readables(Format.HINTED_SIGNAL):
            self.user_readback = soft_signal_rw(float, initial_value=xraysource.value)
        super().__init__(name=name)
