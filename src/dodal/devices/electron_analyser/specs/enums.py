from ophyd_async.core import StrictEnum


class AcquisitionMode(StrictEnum):
    """
    Enumeration of possible acquisition modes for the electron analyser.

    Attributes:
        FIXED_TRANSMISSION: Acquisition mode where the transmission is fixed.
        SNAPSHOT: Acquisition mode for capturing a snapshot.
        FIXED_RETARDING_RATIO: Acquisition mode with a fixed retarding ratio.
        FIXED_ENERGY: Acquisition mode with a fixed energy setting.
    """

    FIXED_TRANSMISSION = "Fixed Transmission"
    SNAPSHOT = "Snapshot"
    FIXED_RETARDING_RATIO = "Fixed Retarding Ratio"
    FIXED_ENERGY = "Fixed Energy"
