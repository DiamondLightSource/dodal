from ophyd_async.core import (
    StandardReadable,
    StrictEnum,
    soft_signal_r_and_setter,
)
from ophyd_async.core import StandardReadableFormat as Format


class LabXraySource(StrictEnum):
    AL_KALPHA = 1486.6
    MG_KALPHA = 1253.6


class LabXraySourceReadable(StandardReadable):
    """Simple device to get the laboratory x-ray tube energy reading"""

    def __init__(self, xraysource: LabXraySource, name: str = "") -> None:
        with self.add_children_as_readables(Format.CONFIG_SIGNAL):
            self.user_readback, _ = soft_signal_r_and_setter(
                float, initial_value=xraysource.value, units="eV"
            )
        super().__init__(name)
