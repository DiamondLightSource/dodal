from pydantic import Field

from dodal.devices.electron_analyser.base_region import BaseRegion, BaseSequence


class SpecsRegion(BaseRegion):
    # Override base class with defaults
    lensMode: str = "SmallArea"
    passEnergy: int | float = 5.0
    acquisitionMode: str = "Fixed Transmission"
    lowEnergy: float = Field(default=800, alias="startEnergy")
    highEnergy: float = Field(default=850, alias="endEnergy")
    stepTime: float = Field(default=1.0, alias="exposureTime")
    energyStep: float = Field(default=0.1, alias="stepEnergy")
    # Specific to this class
    values: float = 1
    centreEnergy: float = 0
    psuMode: str = "1.5keV"
    acquisitionMode: str = ""
    estimatedTimeInMs: float = 0


class SpecsSequence(BaseSequence):
    regions: list[SpecsRegion] = Field(default_factory=lambda: [])
