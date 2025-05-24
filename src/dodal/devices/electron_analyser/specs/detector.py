from dodal.devices.electron_analyser.abstract.base_detector import (
    ElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.specs.driver_io import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.specs.region import SpecsRegion, SpecsSequence


class SpecsDetector(
    ElectronAnalyserDetector[SpecsAnalyserDriverIO, SpecsSequence, SpecsRegion]
):
    def __init__(self, prefix: str, name: str):
        super().__init__(prefix, name, SpecsSequence, SpecsAnalyserDriverIO)
