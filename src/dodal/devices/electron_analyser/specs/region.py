from pydantic import Field

from dodal.devices.electron_analyser.abstract.base_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
)
from dodal.devices.electron_analyser.specs.enums import AcquisitionMode


class SpecsRegion(AbstractBaseRegion[AcquisitionMode]):
    # Override base class with defaults
    lens_mode: str = "SmallArea"
    pass_energy: int = 5
    acquisition_mode: AcquisitionMode = AcquisitionMode.FIXED_TRANSMISSION
    low_energy: float = Field(default=800, alias="start_energy")
    high_energy: float = Field(default=850, alias="end_energy")
    step_time: float = Field(default=1.0, alias="exposure_time")
    energy_step: float = Field(default=0.1, alias="step_energy")
    # Specific to this class
    values: int = 1
    centre_energy: float = 0
    psu_mode: str = "1.5keV"
    estimated_time_in_ms: float = 0


class SpecsSequence(AbstractBaseSequence[SpecsRegion]):
    regions: list[SpecsRegion] = Field(default_factory=lambda: [])
