from typing import Annotated as A

from ophyd_async.core import SignalRW, StrictEnum
from ophyd_async.epics import adcore
from ophyd_async.epics.core import PvSuffix


class PressureJumpCellTriggerMode(StrictEnum):
    INTERNAL = "Internal"
    EXTERNAL = "Exernal"


class PressureJumpCellAdcTriggerMode(StrictEnum):
    SINGLE = "Single"
    MULTIPLE = "Multiple"
    CONTINUOUS = "Continuous"


class PressureJumpCellDriverIO(adcore.ADBaseIO):
    trigger_mode: A[SignalRW[PressureJumpCellTriggerMode], PvSuffix.rbv("TriggerMode")]


class PressureJumpCellAdcIO(adcore.ADBaseIO):
    trigger_mode: A[SignalRW[PressureJumpCellAdcTriggerMode], PvSuffix.rbv("TriggerMode")]

