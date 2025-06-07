from ophyd_async.core import StrictEnum


class Status(StrictEnum):
    READY = "Ready"
    RUNNING = "Running"
    COMPLETED = "Completed"
    INVALID = "Invalid"
    ABORTED = "Aborted"


class DetectorMode(StrictEnum):
    ADC = "ADC"
    PULSE_COUNTING = "Pulse Counting"


class AcquisitionMode(StrictEnum):
    SWEPT = "Swept"
    FIXED = "Fixed"
