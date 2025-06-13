from ophyd_async.core import StrictEnum

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
from dodal.devices.electron_analyser.specs.detector import (
    SpecsAnalyserDriverIO,
    SpecsDetector,
)
from dodal.devices.electron_analyser.vgscienta.detector import (
    VGScientaAnalyserDriverIO,
    VGScientaDetector,
)

# Alias names so can read the type placements easier
AcquisitionMode = StrictEnum
LensMode = StrictEnum
ElectronAnalyserDetectorImpl = VGScientaDetector[LensMode] | SpecsDetector[LensMode]
ElectronAnalyserDriverImpl = (
    VGScientaAnalyserDriverIO[LensMode] | SpecsAnalyserDriverIO[LensMode]
)

GenericElectronAnalyserDetector = ElectronAnalyserDetector[
    AbstractAnalyserDriverIO[AbstractBaseRegion, AcquisitionMode, LensMode],
    AbstractBaseSequence[AbstractBaseRegion],
    AbstractBaseRegion,
]

GenericElectronAnalyserRegionDetector = ElectronAnalyserRegionDetector[
    AbstractAnalyserDriverIO[AbstractBaseRegion, AcquisitionMode, LensMode],
    AbstractBaseRegion,
]
