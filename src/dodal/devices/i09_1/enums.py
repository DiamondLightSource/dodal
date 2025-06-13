from ophyd_async.core import StrictEnum


class LensMode(StrictEnum):
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
