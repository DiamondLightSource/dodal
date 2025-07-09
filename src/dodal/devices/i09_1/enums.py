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
    NOT_CONNECTED = "Not connected"
