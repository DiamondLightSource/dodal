from typing import Generic

from pydantic import Field

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
    low_energy: float = Field(default=800, alias="start_energy")
    centre_energy: float = 0
    high_energy: float = Field(default=850, alias="end_energy")
    acquire_time: float = Field(default=1.0, alias="exposure_time")
    energy_step: float = Field(default=0.1, alias="step_energy")

    # Specific to this class
    values: int = 1
    psu_mode: TPsuMode
    estimated_time_in_ms: float = 0


class SpecsSequence(
    AbstractBaseSequence[SpecsRegion[TLensMode, TPsuMode]], Generic[TLensMode, TPsuMode]
):
    regions: list[SpecsRegion[TLensMode, TPsuMode]] = Field(default_factory=lambda: [])
