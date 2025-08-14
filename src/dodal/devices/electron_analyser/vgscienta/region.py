import uuid
from typing import Generic

from pydantic import Field, field_validator

from dodal.devices.electron_analyser.abstract.base_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
)
from dodal.devices.electron_analyser.abstract.types import (
    TLensMode,
    TPassEnergyEnum,
    TPsuMode,
)
from dodal.devices.electron_analyser.vgscienta.enums import (
    AcquisitionMode,
    DetectorMode,
)


class VGScientaRegion(
    AbstractBaseRegion[AcquisitionMode, TLensMode, TPassEnergyEnum],
    Generic[TLensMode, TPassEnergyEnum],
):
    # Override defaults of base region class
    lens_mode: TLensMode
    pass_energy: TPassEnergyEnum
    acquisition_mode: AcquisitionMode = AcquisitionMode.SWEPT
    low_energy: float = 8.0
    centre_energy: float = Field(alias="fix_energy", default=9)
    high_energy: float = 10.0
    acquire_time: float = Field(default=1.0, alias="step_time")
    energy_step: float = Field(default=200.0)
    # Specific to this class
    id: str = Field(default=str(uuid.uuid4()), alias="region_id")
    total_steps: float = 13.0
    total_time: float = 13.0
    min_x: int = Field(alias="first_x_channel", default=1)
    sensor_max_size_x: int = Field(alias="last_x_channel", default=1000)
    min_y: int = Field(alias="first_y_channel", default=101)
    sensor_max_size_y: int = Field(alias="last_y_channel", default=800)
    detector_mode: DetectorMode = DetectorMode.ADC

    @property
    def size_x(self) -> int:
        return self.sensor_max_size_x - self.min_x + 1

    @property
    def size_y(self) -> int:
        return self.sensor_max_size_y - self.min_y + 1

    @field_validator("pass_energy", mode="before")
    @classmethod
    def validate_pass_energy(cls, val):
        # This is needed because if the value is a number, it can't be casted to the
        # enum correctly.
        return str(val)


class VGScientaSequence(
    AbstractBaseSequence[VGScientaRegion[TLensMode, TPassEnergyEnum]],
    Generic[TLensMode, TPsuMode, TPassEnergyEnum],
):
    psu_mode: TPsuMode = Field(alias="element_set")
    regions: list[VGScientaRegion[TLensMode, TPassEnergyEnum]] = Field(
        default_factory=lambda: []
    )
