from ophyd_async.core import StrictEnum


class DetectorMode(StrictEnum):
    """
    Enumeration of detector operation modes for the electron analyser.

    Attributes:
        ADC: Analog-to-Digital Converter mode.
        PULSE_COUNTING: Pulse Counting mode.
    """

    ADC = "ADC"
    PULSE_COUNTING = "Pulse Counting"


class AcquisitionMode(StrictEnum):
    """
    Enumeration of acquisition modes for the electron analyser.

    Attributes:
        SWEPT: Acquisition mode where the analyser sweeps through a range of values.
        FIXED: Acquisition mode where the analyser remains at a fixed value.
    """

    SWEPT = "Swept"
    FIXED = "Fixed"
