import uuid
from typing import Generic

from pydantic import AliasChoices, Field


from dodal.devices.electron_analyser.abstract.base_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
    JavaToPythonModel,
)
from dodal.devices.electron_analyser.abstract.types import (
    TLensMode,
    TPassEnergyEnum,
    TPsuMode,
)
from dodal.devices.electron_analyser.vgscienta.enums import (
    AcquisitionMode,
    DetectorMode,
    Status,
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
    high_energy: float = 10.0
    acquire_time: float = Field(
        default=1.0, validation_alias=AliasChoices("step_time", "acquire_time")
    )
    energy_step: float = Field(default=200.0)
    # Specific to this class
    id: str = Field(
        default=str(uuid.uuid4()), validation_alias=AliasChoices("region_id", "id")
    )
    fix_energy: float = 9.0
    total_steps: float = 13.0
    total_time: float = 13.0
    first_x_channel: int = 1
    last_x_channel: int = 1000
    first_y_channel: int = 101
    last_y_channel: int = 800
    detector_mode: DetectorMode = DetectorMode.ADC
    status: Status = Status.READY

    def x_channel_size(self) -> int:
        return self.last_x_channel - self.first_x_channel + 1

    def y_channel_size(self) -> int:
        return self.last_y_channel - self.first_y_channel + 1

    @
    
    
    
    ("pass_energy", mode="before")
    @classmethod
    def validate_pass_energy(cls, val):
        # This is needed because if the value is a number, it can't be casted to the
        # enum correctly.
        return str(val)


class VGScientaExcitationEnergySource(JavaToPythonModel):
    name: str = "source1"
    device_name: str = Field(default="", alias="scannable_name")
    value: float = 0


class VGScientaSequence(
    AbstractBaseSequence[VGScientaRegion[TLensMode, TPassEnergyEnum]],
    Generic[TLensMode, TPsuMode, TPassEnergyEnum],
):
    psu_mode: TPsuMode = Field(alias="element_set")
    excitation_energy_sources: list[VGScientaExcitationEnergySource] = Field(
        default_factory=lambda: []
    )
    regions: list[VGScientaRegion[TLensMode, TPassEnergyEnum]] = Field(
        default_factory=lambda: []
    )

    def get_excitation_energy_source_by_region(
        self, region: VGScientaRegion[TLensMode, TPassEnergyEnum]
    ) -> VGScientaExcitationEnergySource:
        value = next(
            (
                e
                for e in self.excitation_energy_sources
                if region.excitation_energy_source == e.name
            ),
            None,
        )
        if value is None:
            raise ValueError(
                f'Unable to find excitation energy source using region "{region.name}"'
            )
        return value
