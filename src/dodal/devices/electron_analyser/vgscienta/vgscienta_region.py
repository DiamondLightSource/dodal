import uuid
from enum import Enum

from pydantic import BaseModel, Field

from dodal.devices.electron_analyser.base_region import BaseRegion


class Status(str, Enum):
    READY = "Ready"
    RUNNING = "Running"
    COMPLETED = "Completed"
    INVALID = "Invalid"
    ABORTED = "Aborted"


class DetectorMode(str, Enum):
    ADC = "ADC"
    PULSE_COUNTING = "Pulse counting"


class EnergyMode(str, Enum):
    KINETIC = "Kinetic"
    BINDING = "Binding"


class AcquisitionMode(str, Enum):
    SWEPT = "Swept"
    FIXED = "Fixed"


class VGScientaRegion(BaseRegion):
    # Override defaults of base region class
    lensMode: str = "Angular45"
    passEnergy: int | float = 5
    acquisitionMode: str = AcquisitionMode.SWEPT
    lowEnergy: float = 8.0
    highEnergy: float = 10.0
    stepTime: float = 1.0
    energyStep: float = Field(default=200.0, alias="stepEnergy")
    # Specific to this class
    regionId: str = Field(default=str(uuid.uuid4()))
    excitationEnergySource: str = "source1"
    energyMode: EnergyMode = EnergyMode.KINETIC
    fixEnergy: float = 9.0
    totalSteps: float = 13.0
    totalTime: float = 13.0
    exposureTime: float = 1.0
    firstXChannel: int = 1
    lastXChannel: int = 1000
    firstYChannel: int = 101
    lastYChannel: int = 800
    detectorMode: DetectorMode = DetectorMode.ADC
    status: Status = Status.READY


class VGScientaExcitationEnergySource(BaseModel):
    name: str = "source1"
    scannableName: str = ""
    value: float = 0


class VGScientaSequence(BaseModel):
    elementSet: str = Field(default="Unknown")
    excitationEnergySources: list[VGScientaExcitationEnergySource] = Field(
        default_factory=lambda: []
    )
    regions: list[VGScientaRegion] = Field(default_factory=lambda: [])

    def get_enabled_regions(self) -> list[VGScientaRegion]:
        return [r for r in self.regions if r.enabled]

    def get_region_names(self) -> list[str]:
        return [r.name for r in self.regions]

    def get_excitation_energy_source_by_region(
        self, region: VGScientaRegion
    ) -> VGScientaExcitationEnergySource | None:
        filtered_excitation_energy_sources = [
            e
            for e in self.excitationEnergySources
            if e.name == region.excitationEnergySource
        ]
        return (
            filtered_excitation_energy_sources[0]
            if len(filtered_excitation_energy_sources) == 1
            else None
        )
