from typing import Generic

from pydantic import AliasChoices, Field

from dodal.devices.electron_analyser.abstract.base_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
)
from dodal.devices.electron_analyser.abstract.types import TLensMode, TPsuMode
from dodal.devices.electron_analyser.specs.enums import AcquisitionMode


class SpecsRegion(
    AbstractBaseRegion[AcquisitionMode, TLensMode, float],
    Generic[TLensMode, TPsuMode],
):
    # Override base class with defaults
    lens_mode: TLensMode
    pass_energy: float = 5
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
    centre_energy: float = 0
    psu_mode: TPsuMode
    estimated_time_in_ms: float = 0


class SpecsSequence(
    AbstractBaseSequence[SpecsRegion[TLensMode, TPsuMode]], Generic[TLensMode, TPsuMode]
):
    regions: list[SpecsRegion[TLensMode, TPsuMode]] = Field(default_factory=lambda: [])
