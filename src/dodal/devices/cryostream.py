from ophyd_async.core import StandardReadable, StrictEnum
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw


class InOut(StrictEnum):
    IN = "In"
    OUT = "Out"


class CryoStream(StandardReadable):
    def __init__(self, prefix: str, name: str = ""):
        self.course = epics_signal_rw(InOut, f"{prefix}-EA-CJET-01:COARSE:CTRL")
        self.fine = epics_signal_rw(InOut, f"{prefix}-EA-CJET-01:FINE:CTRL")
        self.temperature_k = epics_signal_r(float, f"{prefix}-EA-CSTRM-01:TEMP")
        self.back_pressure_bar = epics_signal_r(
            float, f"{prefix}-EA-CSTRM-01:BACKPRESS"
        )

        super().__init__(name)
