from ophyd_async.core import (
    Device,
)
from ophyd_async.epics.core import (
    epics_signal_rw,
)

from dodal.devices.current_amplifiers import (
    Femto3xxGainTable,
    Femto3xxGainToCurrentTable,
    Femto3xxRaiseTime,
    FemtoDDPCA,
)


class DiagnosticDet(Device):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.drain_current_amp = FemtoDDPCA(
            prefix=prefix,
            suffix="GAIN",
            gain_table=Femto3xxGainTable,
            gain_to_current_table=Femto3xxGainToCurrentTable,
            raise_timetable=Femto3xxRaiseTime,
        )
        self.drain_counter = epics_signal_rw(float, f"{prefix}I")
        super().__init__(name=name)
