from ophyd_async.core import StrictEnum


class AcquisitionMode(StrictEnum):
    FIXED_TRANSMISSION = "Fixed Transmission"
    SNAPSHOT = "Snapshot"
    FIXED_RETARDING_RATIO = "Fixed Retarding Ratio"
    FIXED_ENERGY = "Fixed Energy"


class PsuMode(StrictEnum):
    V3500 = "3.5kV"
    V1500 = "1.5kV"
    V400 = "400V"
    V100 = "100V"
    V10 = "10V"
