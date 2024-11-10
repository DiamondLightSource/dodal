from enum import Enum

from ophyd_async.core import SubsetEnum
from ophyd_async.epics import adcore
from ophyd_async.epics.signal import epics_signal_rw_rbv


class PressureJumpCellTriggerMode(str, Enum):
    internal = "Internal"
    external = "Exernal"

class PressureJumpCellAdcTriggerMode(str, Enum):
    single = "Single"
    multiple = "Multiple"
    continuous = "Continuous"

class PressureJumpCellDriverIO(adcore.ADBaseIO):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.trigger_mode = epics_signal_rw_rbv(
            PressureJumpCellTriggerMode, prefix + "TriggerMode"
        )
        super().__init__(prefix, name=name)

class PressureJumpCellAdcIO(adcore.ADBaseIO):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.adc_trigger_mode = epics_signal_rw_rbv(
            PressureJumpCellAdcTriggerMode, prefix + "TriggerMode"
        )
        super().__init__(prefix, name=name)
