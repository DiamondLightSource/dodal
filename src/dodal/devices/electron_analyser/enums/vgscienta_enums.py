from ophyd_async.core import StrictEnum


class VGScientaDetectorMode(StrictEnum):
    ADC = "ADC"
    PULSE_COUNTING = "Pulse Counting"


class VGScientaAcquisitionMode(StrictEnum):
    SWEPT = "Swept"
    FIXED = "Fixed"
