from ophyd_async.core import StrictEnum


class DetectorMode(StrictEnum):
    ADC = "ADC"
    PULSE_COUNTING = "Pulse Counting"


class AcquisitionMode(StrictEnum):
    SWEPT = "Swept"
    FIXED = "Fixed"
