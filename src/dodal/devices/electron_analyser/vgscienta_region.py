import uuid
from enum import Enum

from ophyd_async.core import StrictEnum
from pydantic import BaseModel, Field

from dodal.devices.electron_analyser.base_region import BaseRegion, BaseSequence


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


class VGScientaRegion(BaseRegion):
    # Override defaults of base region class
    lensMode: str = "Angular45"
    passEnergy: int | float = 5
    acquisitionMode: str = AcquisitionMode.SWEPT
    lowEnergy: float = 8.0
    highEnergy: float = 10.0
    stepTime: float = 1.0
    energyStep: float = Field(default=200.0)
    # Specific to this class
    regionId: str = Field(default=str(uuid.uuid4()))
    excitationEnergySource: str = "source1"
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

    def get_energy_step_eV(self) -> float:
        return self.energyStep / 1000

    def x_channel_size(self) -> int:
        return self.lastXChannel - self.firstXChannel + 1

    def y_channel_size(self) -> int:
        return self.lastYChannel - self.firstYChannel + 1


class VGScientaExcitationEnergySource(BaseModel):
    name: str = "source1"
    scannableName: str = ""
    value: float = 0


class VGScientaSequence(BaseSequence[VGScientaRegion]):
    elementSet: str = Field(default="Unknown")
    excitationEnergySources: list[VGScientaExcitationEnergySource] = Field(
        default_factory=lambda: []
    )
    regions: list[VGScientaRegion] = Field(default_factory=lambda: [])

    def get_excitation_energy_source_by_region(
        self, region: VGScientaRegion
    ) -> VGScientaExcitationEnergySource:
        filtered_excitation_energy_sources = [
            e
            for e in self.excitationEnergySources
            if e.name == region.excitationEnergySource
        ]
        n_matches = len(filtered_excitation_energy_sources)
        if not n_matches == 1:
            raise Exception(
                "Should have found 1 match, instead found " + str(n_matches)
            )
        return filtered_excitation_energy_sources[0]
