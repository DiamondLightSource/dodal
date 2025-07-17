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
