from ophyd_async.core import StrictEnum, SupersetEnum

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
LensMode = SupersetEnum | StrictEnum
PsuMode = SupersetEnum | StrictEnum
ElectronAnalyserDetectorImpl = (
    VGScientaDetector[LensMode, PsuMode] | SpecsDetector[LensMode, PsuMode]
)
ElectronAnalyserDriverImpl = (
    VGScientaAnalyserDriverIO[LensMode, PsuMode]
    | SpecsAnalyserDriverIO[LensMode, PsuMode]
)

AbstractBaseRegion = AbstractBaseRegion[AcquisitionMode, LensMode]

GenericElectronAnalyserDetector = ElectronAnalyserDetector[
    AbstractAnalyserDriverIO[AbstractBaseRegion, AcquisitionMode, LensMode, PsuMode],
    AbstractBaseSequence[AbstractBaseRegion, LensMode],
    AbstractBaseRegion,
]

GenericElectronAnalyserRegionDetector = ElectronAnalyserRegionDetector[
    AbstractAnalyserDriverIO[AbstractBaseRegion, AcquisitionMode, LensMode, PsuMode],
    AbstractBaseRegion,
]
