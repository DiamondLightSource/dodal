from dodal.devices.electron_analyser.detector import (
    ElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.vgscienta.driver_io import (
    VGScientaAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta.region import (
    VGScientaRegion,
    VGScientaSequence,
)


class VGScientaDetector(
    ElectronAnalyserDetector[
        VGScientaAnalyserDriverIO,
        VGScientaSequence,
        VGScientaRegion,
    ]
):
    def __init__(self, prefix: str, name: str = ""):
        driver = VGScientaAnalyserDriverIO(prefix)
        super().__init__(prefix, VGScientaSequence, driver, name)
