import json
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum

from dodal.devices.i09.base_region import AbstractBaseRegion, alias_fields


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


@dataclass(kw_only=True, match_args=False)
class SESRegion(AbstractBaseRegion):
    regionId: str = field(default=str(uuid.uuid4()))
    lensMode: str = "Angular45"
    passEnergy: int = 5
    acquisitionMode: AcquisitionMode = AcquisitionMode.SWEPT
    excitationEnergySource: str = "source1"
    energyMode: EnergyMode = EnergyMode.KINETIC
    lowEnergy: float = 8.0
    highEnergy: float = 10.0
    fixEnergy: float = 9.0
    stepTime: float = 1.0
    totalSteps: float = 13.0
    totalTime: float = 13.0
    energyStep: float = 200.0
    exposureTime: float = 1.0
    firstXChannel: int = 1
    lastXChannel: int = 1000
    firstYChannel: int = 101
    lastYChannel: int = 800
    detectorMode: DetectorMode = DetectorMode.ADC
    status: Status = Status.READY


@dataclass
class SESExcitationEnergySource:
    name: str = "source1"
    scannableName: str = ""
    value: float = 0


@dataclass
class SESSequence:
    elementSet: str = field(default="Unknown")
    excitationEnergySources: list[SESExcitationEnergySource] = field(
        default_factory=lambda: []
    )
    regions: list[SESRegion] = field(default_factory=lambda: [])

    def get_enabled_regions(self) -> list[SESRegion]:
        return [r for r in self.regions if r.enabled]

    def get_region_names(self) -> list[str]:
        return [r.name for r in self.regions]

    def get_excitation_energy_source_by_region(
        self, region: SESRegion
    ) -> SESExcitationEnergySource | None:
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


class SESSequenceHelper:
    @staticmethod
    def load_sequence(sequence_file: str) -> SESSequence:
        with open(sequence_file) as f:
            json_obj = json.load(f)
            sequence = SESSequence(**json_obj)
            # Standard json libray doesn't convert nested classes so must do this ourselves
            sequence.regions = [
                SESRegion(**alias_fields(r)) if isinstance(r, dict) else r
                for r in sequence.regions
            ]
            sequence.excitationEnergySources = [
                SESExcitationEnergySource(**e) if isinstance(e, dict) else e
                for e in sequence.excitationEnergySources
            ]
            return sequence

    @staticmethod
    def save_sequence(sequence: SESSequence, sequence_file: str) -> None:
        with open(sequence_file, "w") as f:
            f.write(json.dumps(asdict(sequence)))


if __name__ == "__main__":
    print("===START===")

    sequence_file1 = "/scratch/gda_development/gda-master-default/eclipse/gda_data_non_live/2025/0-0/xml/user.seq"
    sequence_file2 = "/scratch/gda_development/gda-master-default/eclipse/gda_data_non_live/2025/0-0/xml/save_test.seq"

    sequence = SESSequenceHelper.load_sequence(sequence_file1)

    test_region = SESRegion()
    print(test_region)
    print(sequence)
    SESSequenceHelper.save_sequence(sequence, sequence_file2)

    print(sequence.regions)
    print(sequence.get_excitation_energy_source_by_region(sequence.regions[0]))
    SESSequence()

    print(sequence.get_region_names())

    print("===END===")
