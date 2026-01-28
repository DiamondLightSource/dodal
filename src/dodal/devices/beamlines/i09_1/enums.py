from ophyd_async.core import SupersetEnum


class LensMode(SupersetEnum):
    LARGE_AREA = "LargeArea"
    MEDIUM_ANGULAR_DISPERSION = "MediumAngularDispersion"
    MEDIUM_AREA = "MediumArea"
    SMALL_AREA = "SmallArea"
    HIGH_MAGNIFICATION = "HighMagnification"
    LOW_ANGULAR_DISPERSION = "LowAngularDispersion"
    LOW_ANGULAR_DISPERSION2 = "LowAngularDispersion2"
    HIGH_ANGULAR_DISPERSION = "HighAngularDispersion"
    WIDE_ANGLE_MODE = "WideAngleMode"
    MEDIUM_ANGLE_MODE = "MediumAngleMode"
    MEDIUM_MAGNIFICATION = "MediumMagnification"
    LOW_MAGNIFICATION = "LowMagnification"
    HIGH_MAGNIFICATION2 = "HighMagnification2"
    RAMP_MODE = "RampMode"
    # This is connected to the device separately and will only have "Not connected" as
    # option if disconnected. Once it is connected, "Not connected" is replaced with the
    # options above. This is also why this must be a SupersetEnum.
    NOT_CONNECTED = "Not connected"


class PsuMode(SupersetEnum):
    V3500 = "3.5kV"
    V1500 = "1.5kV"
    V400 = "400V"
    # This is connected to the device separately and will only have "Not connected" as
    # option if disconnected. Once it is connected, "Not connected" is replaced with the
    # options above. This is also why this must be a SupersetEnum.
    NOT_CONNECTED = "Not connected"
