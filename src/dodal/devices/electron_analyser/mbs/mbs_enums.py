from ophyd_async.core import StrictEnum


class AcquisitionMode(StrictEnum):
    FIXED = "Fixed"
    SWEPT = "Swept"
    DITHER = "Dither"
