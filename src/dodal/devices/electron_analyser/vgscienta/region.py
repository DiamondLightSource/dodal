import uuid
from enum import Enum

from ophyd_async.core import StrictEnum
from pydantic import Field

from dodal.devices.electron_analyser.abstract.base_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
    JavaToPythonModel,
)


class Status(str, Enum):
    READY = "Ready"
    RUNNING = "Running"
    COMPLETED = "Completed"
    INVALID = "Invalid"
    ABORTED = "Aborted"


class DetectorMode(StrictEnum):
    ADC = "ADC"
    PULSE_COUNTING = "Pulse Counting"


class AcquisitionMode(str, Enum):
    SWEPT = "Swept"
    FIXED = "Fixed"


class VGScientaRegion(AbstractBaseRegion):
    # Override defaults of base region class
    lens_mode: str = "Angular45"
    pass_energy: int = 5
    acquisition_mode: str = AcquisitionMode.SWEPT
    low_energy: float = 8.0
    high_energy: float = 10.0
    step_time: float = 1.0
    energy_step: float = Field(default=200.0)
    # Specific to this class
    id: str = Field(default=str(uuid.uuid4()), alias="region_id")
    excitation_energy_source: str = "source1"
    fix_energy: float = 9.0
    total_steps: float = 13.0
    total_time: float = 13.0
    exposure_time: float = 1.0
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


class VGScientaExcitationEnergySource(JavaToPythonModel):
    name: str = "source1"
    device_name: str = Field(default="", alias="scannable_name")
    value: float = 0


class VGScientaSequence(AbstractBaseSequence[VGScientaRegion]):
    element_set: str = Field(default="Unknown")
    excitation_energy_sources: list[VGScientaExcitationEnergySource] = Field(
        default_factory=lambda: []
    )
    regions: list[VGScientaRegion] = Field(default_factory=lambda: [])

    def get_excitation_energy_source_by_region(
        self, region: VGScientaRegion
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
