from dodal.devices.electron_analyser.abstract.base_detector import (
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
        super().__init__(prefix, VGScientaSequence, VGScientaAnalyserDriverIO, name)
