from ophyd_async.core import StrictEnum


class AcquisitionMode(StrictEnum):
    FIXED = "FIXED"
    SWEPT = "SWEPT"
    DITHER = "DITHER"
