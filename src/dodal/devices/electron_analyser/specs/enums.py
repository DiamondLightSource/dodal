from ophyd_async.core import StrictEnum


class AcquisitionMode(StrictEnum):
    FIXED_TRANSMISSION = "Fixed Transmission"
    SNAPSHOT = "Snapshot"
    FIXED_RETARDING_RATIO = "Fixed Retarding Ratio"
    FIXED_ENERGY = "Fixed Energy"
