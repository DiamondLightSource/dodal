from typing import Generic

from pydantic import Field

from dodal.devices.electron_analyser.abstract.base_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
    TLensMode,
)
from dodal.devices.electron_analyser.specs.enums import AcquisitionMode


class SpecsRegion(AbstractBaseRegion[AcquisitionMode, TLensMode], Generic[TLensMode]):
    # Override base class with defaults
    lens_mode: TLensMode
    pass_energy: int = 5
    acquire_time: float = 1.0
    acquisition_mode: AcquisitionMode = AcquisitionMode.FIXED_TRANSMISSION
    low_energy: float = Field(default=800, alias="start_energy")
    high_energy: float = Field(default=850, alias="end_energy")
    energy_step: float = Field(default=0.1, alias="step_energy")
    # Specific to this class
    values: int = 1
    centre_energy: float = 0
    # ToDo - Update to an enum https://github.com/DiamondLightSource/dodal/issues/1328
    psu_mode: str = "1.5kV"
    estimated_time_in_ms: float = 0


class SpecsSequence(AbstractBaseSequence[SpecsRegion, TLensMode], Generic[TLensMode]):
    regions: list[SpecsRegion[TLensMode]] = Field(default_factory=lambda: [])
