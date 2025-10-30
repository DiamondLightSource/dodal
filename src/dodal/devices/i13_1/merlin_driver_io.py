from typing import Annotated as A

from ophyd_async.core import SignalRW, StrictEnum
from ophyd_async.epics import adcore
from ophyd_async.epics.core import PvSuffix


class MerlinTriggerMode(StrictEnum):
    """Trigger modes for ADMerlin."""

    INTERNAL = "Internal"
    ENABLE = "Trigger Enable"
    START_RISING = "Trigger start rising"
    START_FALLING = "Trigger start falling"
    BOTH_RISING = "Trigger both rising"
    LVDS_ENABLE = "LVDS Trig Enable"
    LVDS_START_RISING = "LVDS Trig start rising"
    LVDS_START_FALLING = "LVDS Trig start falling"
    LVDS_BOTH_RISING = "LVDS Trig both rising"
    SOFTWARE = "Software"


class MerlinDriverIO(adcore.ADBaseIO):
    """Driver for Merlin detectors"""

    trigger_mode: A[SignalRW[MerlinTriggerMode], PvSuffix.rbv("TriggerMode")]
