from ophyd_async.core import StrictEnum


class MagnetModes(StrictEnum):
    UNIAXIAL_X = "UNIAXIAL_X"
    UNIAXIAL_Y = "UNIAXIAL_Y"
    UNIAXIAL_Z = "UNIAXIAL_Z"
    SPHERICAL = "SPHERICAL"
    PLANAR_XZ = "PLANAR_XZ"
    QUADRANT_XY = "QUADRANT_XY"
    CUBIC = "CUBIC"
    UNDEFINED = "UNDEFINED"


class MagnetRampStatus(StrictEnum):
    RAMP_MADE = "RAMP MADE"
    RAMPING = "RAMPING"


class MagnetLimitStatus(StrictEnum):
    OK = "OK"
    VIOLATION = "VIOLATION"
