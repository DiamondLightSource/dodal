from .coordinates import (
    MagnetPosition,
    MagnetRequest,
    MagnetSphericalPosition,
    MagnetSphericalRequest,
)
from .movement import MagnetPositionError
from .power_supply import MagnetAxisPowerSupply, ThreeMagnetAxisPowerSupply
from .ramp_controller import MagnetAxisRampRateController
from .superconducting_magnet import (
    FlyMagnetInfo,
    MagnetAxis,
    MagnetLimitStatus,
    MagnetMode,
    MagnetRampStatus,
    MockSuperConductingMagnetController,
    SuperConductingMagnetController,
)

__all__ = [
    "MagnetPosition",
    "MagnetSphericalPosition",
    "MagnetSphericalRequest",
    "MagnetRequest",
    "MagnetPositionError",
    "MagnetAxisRampRateController",
    "MagnetAxisPowerSupply",
    "ThreeMagnetAxisPowerSupply",
    "FlyMagnetInfo",
    "MagnetAxis",
    "MagnetLimitStatus",
    "MagnetMode",
    "MagnetRampStatus",
    "MockSuperConductingMagnetController",
    "SuperConductingMagnetController",
]
