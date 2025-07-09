from ophyd_async.core import StrictEnum, SupersetEnum


class AcquisitionMode(StrictEnum):
    FIXED_TRANSMISSION = "Fixed Transmission"
    SNAPSHOT = "Snapshot"
    FIXED_RETARDING_RATIO = "Fixed Retarding Ratio"
    FIXED_ENERGY = "Fixed Energy"


class PsuMode(SupersetEnum):
    V3500 = "3.5kV"
    V1500 = "1.5kV"
    V400 = "400V"
    V100 = "100V"  # B07 only?
    V40 = "40V"  # Only for I09-1 SIMULATOR
    V10 = "10V"  # B07 only?
    # This is connected to the device separately and will only have "Not connected" as
    # option if disconnected. Once it is connected, "Not connected" is replaced with the
    # options above. This is also why this must be a SupersetEnum.
    NOT_CONNECTED = "Not connected"
