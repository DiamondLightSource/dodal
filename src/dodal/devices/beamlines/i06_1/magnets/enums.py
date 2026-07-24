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

    @property
    def axis_alias(self) -> str:
        match self:
            case MagnetModes.UNIAXIAL_X:
                return "x"
            case MagnetModes.UNIAXIAL_Y:
                return "y"
            case MagnetModes.UNIAXIAL_Z:
                return "z"
            case _:
                raise ValueError(f"Invalid uniaxial mode {self}")


class MagnetRampStatus(StrictEnum):
    RAMP_MADE = "RAMP MADE"
    RAMPING = "RAMPING"


class MagnetLimitStatus(StrictEnum):
    OK = "OK"
    VIOLATION = "VIOLATION"
