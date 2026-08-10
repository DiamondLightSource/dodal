from ophyd_async.core import StrictEnum


class AcquisitionMode(StrictEnum):
    FIXED = "Fixed"
    FIXED_TRIGD = "FixedTrigd"
    SWEPT = "Swept"
    DITHER = "Dither"
