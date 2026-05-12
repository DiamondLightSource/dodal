from typing import Generic

from pydantic import Field

from dodal.devices.electron_analyser.base.base_region import (
    BaseRegion,
    TLensMode,
    TPassEnergy,
    TPsuMode,
)
from dodal.devices.electron_analyser.mbs.mbs_enums import AcquisitionMode


class MbsRegion(
    BaseRegion[AcquisitionMode, TLensMode, TPassEnergy],
    Generic[TLensMode, TPsuMode, TPassEnergy],
):
    # Override base class with defaults
    lens_mode: TLensMode
    pass_energy: TPassEnergy
    acquisition_mode: AcquisitionMode = AcquisitionMode.FIXED
    low_energy: float = Field(default=800, alias="start_energy")
    high_energy: float = Field(default=850, alias="end_energy")
    centre_energy: float = Field(
        default_factory=lambda data: (data["high_energy"] + data["low_energy"]) / 2
    )
    acquire_time: float = Field(default=1.0, alias="time_per_step")
    energy_step: float = Field(default=0.1, alias="step_energy")
    # Default is True as mbs ususally only uses one region.
    enabled: bool = True

    # Specific to this class
    deflector_x: float = 0
