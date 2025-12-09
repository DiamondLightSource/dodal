from typing import Generic

from ophyd_async.core import StrictEnum
from pydantic import Field

from dodal.devices.electron_analyser.region.base_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
    TLensMode,
    TPsuMode,
)


class SpecsAcquisitionMode(StrictEnum):
    FIXED_TRANSMISSION = "Fixed Transmission"
    SNAPSHOT = "Snapshot"
    FIXED_RETARDING_RATIO = "Fixed Retarding Ratio"
    FIXED_ENERGY = "Fixed Energy"


class SpecsRegion(
    AbstractBaseRegion[SpecsAcquisitionMode, TLensMode, float],
    Generic[TLensMode, TPsuMode],
):
    # Override base class with defaults
    lens_mode: TLensMode
    pass_energy: float = 5
    acquisition_mode: SpecsAcquisitionMode = SpecsAcquisitionMode.FIXED_TRANSMISSION
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
