from dodal.devices.electron_analyser.abstract.base_detector import (
    AbstractElectronAnalyserDetector,
    AbstractElectronAnalyserRegionDetector,
)
from dodal.devices.electron_analyser.specs.driver_io import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.specs.region import SpecsRegion, SpecsSequence


class SpecsRegionDetector(
    AbstractElectronAnalyserRegionDetector[SpecsAnalyserDriverIO, SpecsRegion]
):
    def configure_region(self):
        # ToDo - Need to move configure plans to here and rewrite tests
        pass


class SpecsDetector(
    AbstractElectronAnalyserDetector[SpecsAnalyserDriverIO, SpecsSequence, SpecsRegion]
):
    def __init__(self, prefix: str, name: str):
        super().__init__(prefix, name, SpecsSequence)

    def _create_driver(self, prefix: str) -> SpecsAnalyserDriverIO:
        return SpecsAnalyserDriverIO(prefix, "driver")

    def _create_region_detector(
        self, driver: SpecsAnalyserDriverIO, region: SpecsRegion
    ) -> SpecsRegionDetector:
        return SpecsRegionDetector(self.name, driver, region)
