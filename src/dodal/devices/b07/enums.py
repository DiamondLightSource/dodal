from ophyd_async.core import StrictEnum, SupersetEnum


class Grating(StrictEnum):
    NI_400 = "400 l/mm Ni"
    NI_1000 = "1000 l/mm Ni"
    PT_600 = "BAD 600 l/mm Pt"
    AU_600 = "600 l/mm Au"
    NO_GRATING = "No Grating"


class LensMode(SupersetEnum):
    LARGE_AREA = "LargeArea"
    HIGH_MAGNIFICATION = "HighMagnification"
    MEDIUM_MAGNIFICATION = "MediumMagnification"
    LOW_MAGNIFICATION = "LowMagnification"
    MEDIUM_ANGULAR_DISPERSION = "MediumAngularDispersion"
    LOW_ANGULAR_DISPERSION = "LowAngularDispersion"
    HIGH_ANGULAR_DISPERSION = "HighAngularDispersion"
    WIDE_ANGLE_MODE = "WideAngleMode"
    MEDIUM_AREA = "MediumArea"
    SMALL_AREA = "SmallArea"
    HIGH_MAGNIFICATION2 = "HighMagnification2"
    # This is connected to the device separately and will only have "Not connected" as
    # option if disconnected. Once it is connected, "Not connected" is replaced with the
    # options above. This is also why this must be a SupersetEnum.
    NOT_CONNECTED = "Not connected"


class PsuMode(SupersetEnum):
    V3500 = "3.5kV"
    V1500 = "1.5kV"
    V400 = "400V"
    V100 = "100V"
    V10 = "10V"
    # This is connected to the device separately and will only have "Not connected" as
    # option if disconnected. Once it is connected, "Not connected" is replaced with the
    # options above. This is also why this must be a SupersetEnum.
    NOT_CONNECTED = "Not connected"
