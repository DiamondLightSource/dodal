from typing import Annotated as A

from ophyd_async.core import SignalRW, StrictEnum
from ophyd_async.epics import adcore
from ophyd_async.epics.core import PvSuffix


class PressureJumpCellTriggerMode(StrictEnum):
    INTERNAL = "Internal"
    EXTERNAL = "Exernal"


class AdcTriggerCondition(StrictEnum):
    THRESHOLD_BELOW = "Below Threshold"
    THRESHOLD_ABOVE = "Above Threshold"
    EDGE_RISING = "Rising Edge"
    EDGE_FALLING = "Falling Edge"
    ALWAYS_ON = "Always On"
    ALWAYS_OFF = "Always Off"


class AdcTriggerMode(StrictEnum):
    IDLE = "Idle"
    ARMED = "Armed"
    GATING = "Gating"
    ACQUIRING = "Acquiring"


class PressureJumpCellDriverIO(adcore.ADBaseIO):
    trigger_mode: A[SignalRW[PressureJumpCellTriggerMode], PvSuffix.rbv("TriggerMode")]


class PressureJumpCellAdcTriggerIO(adcore.NDPluginBaseIO):
    # Trigger Setup
    pre_trigger_samples: A[SignalRW[int], PvSuffix("PRECOUNT")]
    post_trigger_samples: A[SignalRW[int], PvSuffix("POSTCOUNT")]
    trigger_channel: A[SignalRW[int], PvSuffix("TriggerChannel")]
    permit_overlap: A[SignalRW[bool], PvSuffix("PermitOverlap")]
    average_samples: A[SignalRW[bool], PvSuffix("AverageSamples")]

    on_condition: A[SignalRW[AdcTriggerCondition], PvSuffix("TriggerOnCond")]
    on_threshold: A[SignalRW[float], PvSuffix("TriggerOnThresh")]
    off_condition: A[SignalRW[AdcTriggerCondition], PvSuffix("TriggerOffCond")]
    off_threshold: A[SignalRW[float], PvSuffix("TriggerOffThresh")]

    trigger_mode: A[SignalRW[AdcTriggerMode], PvSuffix("TriggerMode")]

    # Trigger Control
    capture: A[SignalRW[bool], PvSuffix("Capture")]
    mode: A[SignalRW[AdcTriggerMode], PvSuffix.rbv("Mode")]
    soft_trigger: A[SignalRW[bool], PvSuffix("Soft_Trigger")]

    buffered_frames: A[SignalRW[int], PvSuffix("BufferFrames")]
    buffered_samples: A[SignalRW[int], PvSuffix("BufferSamples")]
    output_triggers: A[SignalRW[int], PvSuffix.rbv("OutputCount")]
    ignored_triggers: A[SignalRW[int], PvSuffix.rbv("IgnoredCount")]
    status: A[SignalRW[str], PvSuffix("StatusMessage")]
