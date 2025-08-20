from enum import Enum

from ophyd_async.core import (
    StandardReadable,
    soft_signal_r_and_setter,
)


class LabXraySource(float, Enum):
    AL_KALPHA = 1486.6
    MG_KALPHA = 1253.6


class LabXraySourceReadable(StandardReadable):
    """Simple device to get the laboratory x-ray tube energy reading"""

    def __init__(self, xraysource: LabXraySource, name: str = "") -> None:
        with self.add_children_as_readables():
            self.energy_ev, _ = soft_signal_r_and_setter(
                float, initial_value=xraysource.value, units="eV"
            )
        super().__init__(name)
