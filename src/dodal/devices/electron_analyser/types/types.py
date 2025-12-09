from ophyd_async.core import StrictEnum, SupersetEnum

from dodal.devices.electron_analyser.detector.base_detector import (
    ElectronAnalyserDetector,
    ElectronAnalyserRegionDetector,
)
from dodal.devices.electron_analyser.detector.specs_detector import (
    SpecsAnalyserDriverIO,
    SpecsDetector,
)
from dodal.devices.electron_analyser.detector.vgscienta_detector import (
    VGScientaAnalyserDriverIO,
    VGScientaDetector,
)
from dodal.devices.electron_analyser.driver_io.base_driver_io import (
    AbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.region.base_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
)

AnyAcqMode = StrictEnum
AnyLensMode = SupersetEnum | StrictEnum
AnyPsuMode = SupersetEnum | StrictEnum
AnyPassEnergy = StrictEnum | float
AnyPassEnergyEnum = StrictEnum

# Electron analyser types that encompasses all implementations, useful for tests and
# plans
ElectronAnalyserDetectorImpl = (
    VGScientaDetector[AnyLensMode, AnyPsuMode, AnyPassEnergyEnum]
    | SpecsDetector[AnyLensMode, AnyPsuMode]
)
ElectronAnalyserDriverImpl = (
    VGScientaAnalyserDriverIO[AnyLensMode, AnyPsuMode, AnyPassEnergyEnum]
    | SpecsAnalyserDriverIO[AnyLensMode, AnyPsuMode]
)

# Short hand the type so less verbose
AbstractBaseRegion = AbstractBaseRegion[AnyAcqMode, AnyLensMode, AnyPassEnergy]

# Generic electron analyser types that supports full typing with the abstract classes.
GenericElectronAnalyserDetector = ElectronAnalyserDetector[
    AbstractAnalyserDriverIO[
        AbstractBaseRegion, AnyAcqMode, AnyLensMode, AnyPsuMode, AnyPassEnergy
    ],
    AbstractBaseSequence[AbstractBaseRegion],
    AbstractBaseRegion,
]

GenericElectronAnalyserRegionDetector = ElectronAnalyserRegionDetector[
    AbstractAnalyserDriverIO[
        AbstractBaseRegion, AnyAcqMode, AnyLensMode, AnyPsuMode, AnyPassEnergy
    ],
    AbstractBaseRegion,
]
