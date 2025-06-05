from dodal.devices.electron_analyser.abstract.base_driver_io import (
    AbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.abstract.base_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
)
from dodal.devices.electron_analyser.detector import (
    ElectronAnalyserDetector,
    ElectronAnalyserRegionDetector,
)
from dodal.devices.electron_analyser.specs.detector import SpecsDetector
from dodal.devices.electron_analyser.vgscienta.detector import VGScientaDetector

ElectronAnalyserDetectorImpl = VGScientaDetector | SpecsDetector

GenericElectronAnalyserDetector = ElectronAnalyserDetector[
    AbstractAnalyserDriverIO[AbstractBaseRegion],
    AbstractBaseSequence,
    AbstractBaseRegion,
]

GenericElectronAnalyserRegionDetector = ElectronAnalyserRegionDetector[
    AbstractAnalyserDriverIO[AbstractBaseRegion], AbstractBaseRegion
]
