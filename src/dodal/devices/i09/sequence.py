import json
import uuid
from dataclasses import dataclass
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

@dataclass
class SESRegion:
    name : str = "Region"
    enabled : bool = False
    regionId : str = uuid.uuid4()
    lensMode : str = "Angular45"
    passEnergy : int = 5
    slices : int = 1
    iterations : int = 1
    acquisitionMode : AcquisitionMode = AcquisitionMode.SWEPT
    excitationEnergySource : str = "source1"
    energyMode : EnergyMode = EnergyMode.KINETIC
    lowEnergy : float = 8
    highEnergy : float = 10
    fixEnergy : float = 9
    stepTime : float = 1
    totalSteps : float = 15
    totalTime : float = 15
    energyStep : float = 200
    exposureTime : float = 1.
    firstXChannel : int = 1
    lastXChannel : int = 1000
    firstYChannel : int = 101
    lastYChannel : int = 800
    detectorMode : DetectorMode = DetectorMode.ADC

    def __init__(self, **args):
        self.status = Status.READY #This shouldn't be serialised

@dataclass
class SESExcitationEnergySource:
    name: str
    scannableName: str
    value : float

@dataclass
class SESSequence:
    elementSet : str
    excitationEnergySources: list[SESExcitationEnergySource]
    regions : list[SESRegion]

class SESSequenceHelper:

    @staticmethod
    def loadSequence(sequence_file : str) -> SESSequence:
        with open(sequence_file) as f:
            json_obj = json.load(f)
            sequence = SESSequence(**json_obj)
            #Standard json libray doesn't convert nested classes so must do this ourselves
            sequence.regions = [SESRegion(**r) for r in sequence.regions]
            sequence.excitationEnergySources = [SESExcitationEnergySource(**e) for e in sequence.excitationEnergySources]
            return sequence

if __name__ == "__main__":
    pass
    print("===START===")

    sequence_file = "/scratch/gda_development/gda-master-default/eclipse/gda_data_non_live/2025/0-0/xml/user.seq"

    sequence = SESSequenceHelper.loadSequence(sequence_file)
    regions = sequence.regions[0]
    print(regions.status)

    print(sequence)
    print("===END===")


