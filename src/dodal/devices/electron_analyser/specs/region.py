from typing import Generic

from pydantic import AliasChoices, Field

from dodal.devices.electron_analyser.abstract.base_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
    TLensMode,
)
from dodal.devices.electron_analyser.specs.enums import AcquisitionMode


class SpecsRegion(AbstractBaseRegion[AcquisitionMode, TLensMode], Generic[TLensMode]):
    # Override base class with defaults
    lens_mode: TLensMode
    pass_energy: int = 10
    acquisition_mode: AcquisitionMode = AcquisitionMode.FIXED_TRANSMISSION
    acquire_time: float = Field(
        default=1.0, validation_alias=AliasChoices("exposure_time", "acquire_time")
    )
    low_energy: float = Field(
        default=500, validation_alias=AliasChoices("start_energy", "low_energy")
    )
    high_energy: float = Field(
        default=510, validation_alias=AliasChoices("end_energy", "high_energy")
    )
    energy_step: float = Field(
        default=0.15, validation_alias=AliasChoices("step_energy", "energy_step")
    )
    # Specific to this class
    values: int = 1
    centre_energy: float = 1.0
    # ToDo - Update to an enum https://github.com/DiamondLightSource/dodal/issues/1328
    psu_mode: str = "1.5kV"
    estimated_time_in_ms: float = 0.1


class SpecsSequence(AbstractBaseSequence[SpecsRegion, TLensMode], Generic[TLensMode]):
    regions: list[SpecsRegion[TLensMode]] = Field(default_factory=lambda: [])
