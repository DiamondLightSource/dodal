from ophyd_async.core import (
    StandardReadableFormat,
)
from ophyd_async.epics.core import (
    epics_signal_r,
)

from dodal.devices.current_amplifiers import (
    Femto3xxGainTable,
    Femto3xxGainToCurrentTable,
    Femto3xxRaiseTime,
    FemtoDDPCA,
)


class DiagnosticDet(FemtoDDPCA):
    def __init__(
        self,
        prefix: str,
        amp_suffix: str = "GAIN",
        counter_suffix: str = "I",
        name: str = "",
    ) -> None:

        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.drain_current = epics_signal_r(float, prefix + counter_suffix)
        super().__init__(
            prefix=prefix,
            suffix=amp_suffix,
            gain_table=Femto3xxGainTable,
            gain_to_current_table=Femto3xxGainToCurrentTable,
            raise_timetable=Femto3xxRaiseTime,
            name=name,
        )
