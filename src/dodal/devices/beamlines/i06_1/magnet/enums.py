from ophyd_async.core import StrictEnum


class MagnetMode(StrictEnum):
    UNIAXIAL_X = "UNIAXIAL_X"
    UNIAXIAL_Y = "UNIAXIAL_Y"
    UNIAXIAL_Z = "UNIAXIAL_Z"
    SPHERICAL = "SPHERICAL"
    PLANAR_XZ = "PLANAR_XZ"
    QUADRANT_XY = "QUADRANT_XY"
    CUBIC = "CUBIC"
    UNDEFINED = "UNDEFINED"

    @property
    def axis_alias(self) -> str:
        match self:
            case MagnetMode.UNIAXIAL_X:
                return "x"
            case MagnetMode.UNIAXIAL_Y:
                return "y"
            case MagnetMode.UNIAXIAL_Z:
                return "z"
            case _:
                raise ValueError(f"{self} is not a valid uniaxial.")


class MagnetRampStatus(StrictEnum):
    RAMP_MADE = "RAMP MADE"
    RAMPING = "RAMPING"


class MagnetLimitStatus(StrictEnum):
    OK = "OK"
    VIOLATION = "VIOLATION"
