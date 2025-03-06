import json
import uuid
from dataclasses import dataclass, field
from enum import Enum


class Status(Enum):
    READY = "Ready"
    RUNNING = "Running"
    COMPLETED = "Completed"
    INVALID = "Invalid"
    ABORTED = "Aborted"

class AcquisitionMode(Enum):
    SWEPT = "Swept"
    FIXED = "Fixed"

class DetectorMode(Enum):
    ADC = "ADC"
    PULSE_COUNTING = "Pulse counting"

class EnergyMode(Enum):
    KINETIC = "Kinetic"
    BINDING = "Binding"

class ToJson:
    def toJSON(self):
        return json.dumps(
            self,
            default=lambda o: o.__dict__,
            sort_keys=True,
            indent=4
        )

@dataclass
class SESRegion(ToJson):
    name : str = field(default = "New_region")
    enabled : bool = field(default = False)
    regionId : str = field(default = str(uuid.uuid4()))
    lensMode : str = field(default = "Angular45")
    passEnergy : int = field(default = 5)
    slices : int = field(default = 1)
    iterations : int = field(default = 1)
    acquisitionMode : AcquisitionMode = field(default = AcquisitionMode.FIXED)
    excitationEnergySource : str = field(default = "source1")
    energyMode : EnergyMode = field(default = EnergyMode.KINETIC)
    lowEnergy : float = field(default = 8)
    highEnergy : float = field(default = 10)
    fixEnergy : float = field(default = 9)
    stepTime : float = field(default = 1)
    totalSteps : float = field(default = 15)
    totalTime : float = field(default = 15)
    energyStep : float = field(default = 200)
    exposureTime : float = field(default = 1)
    firstXChannel : int = field(default = 1)
    lastXChannel : int = field(default = 1000)
    firstYChannel : int = field(default = 101)
    lastYChannel : int = field(default = 800)
    detectorMode : DetectorMode = field(default = DetectorMode.ADC)

@dataclass
class SESExcitationEnergySource(ToJson):
    name: str = field(default="source1")
    scannableName: str = field(default="")
    value : float = field(default=0)

@dataclass
class SESSequence(ToJson):
    elementSet : str = field(default="Unknown")
    excitationEnergySources: list[SESExcitationEnergySource] = field(default_factory = lambda : [])
    regions : list[SESRegion] = field(default_factory = lambda : [])

    def get_enabled_regions(self) -> list[SESRegion]:
        return [r for r in self.regions if r.enabled]

    def get_region_names(self) -> list[str]:
        return [r.name for r in self.regions]

    def get_excitation_energy_source_by_region(self, region: SESRegion)  -> SESExcitationEnergySource | None:
        filtered_excitation_energy_sources = [e for e in self.excitationEnergySources if e.name == region.excitationEnergySource]
        return filtered_excitation_energy_sources[0] if len(filtered_excitation_energy_sources) == 1 else None

class SESSequenceHelper:

    @staticmethod
    def load_sequence(sequence_file : str) -> SESSequence:
        with open(sequence_file) as f:
            json_obj = json.load(f)
            sequence = SESSequence(**json_obj)
            #Standard json libray doesn't convert nested classes so must do this ourselves
            sequence.regions = [SESRegion(**r) if isinstance(r, dict) else r for r in sequence.regions]
            sequence.excitationEnergySources = [SESExcitationEnergySource(**e) if isinstance(e, dict) else e for e in sequence.excitationEnergySources]
            return sequence

    @staticmethod
    def save_sequence(sequence : SESSequence, sequence_file : str) -> None:
        with open(sequence_file, 'w') as f:
            f.write(sequence.toJSON())

if __name__ == "__main__":
    print("===START===")

    sequence_file1 = "/scratch/gda_development/gda-master-default/eclipse/gda_data_non_live/2025/0-0/xml/user.seq"
    sequence_file2 = "/scratch/gda_development/gda-master-default/eclipse/gda_data_non_live/2025/0-0/xml/save_test.seq"

    sequence = SESSequenceHelper.load_sequence(sequence_file1)

    test_region = SESRegion()
    print(test_region)
    print(sequence.toJSON())
    SESSequenceHelper.save_sequence(sequence, sequence_file2)

    print(sequence.get_excitation_energy_source_by_region(sequence.regions[1]))
    SESSequence()

    print(sequence.get_region_names())

    print("===END===")
