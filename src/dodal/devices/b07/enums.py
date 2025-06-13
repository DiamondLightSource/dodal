from ophyd_async.core import StrictEnum


class Grating(StrictEnum):
    NI_400 = "400 l/mm Ni"
    NI_1000 = "1000 l/mm Ni"
    PT_600 = "BAD 600 l/mm Pt"
    AU_600 = "600 l/mm Au"
    NO_GRATING = "No Grating"


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
