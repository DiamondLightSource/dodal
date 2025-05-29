from dodal.devices.electron_analyser.abstract.base_detector import (
    AbstractElectronAnalyserDetector,
    AbstractElectronAnalyserRegionDetector,
)
from dodal.devices.electron_analyser.vgscienta.driver_io import (
    VGScientaAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta.region import (
    VGScientaRegion,
    VGScientaSequence,
)


class VGScientaRegionDetector(
    AbstractElectronAnalyserRegionDetector[VGScientaAnalyserDriverIO, VGScientaRegion]
):
    def configure_region(self):
        # ToDo - Need to move configure plans to here and rewrite tests
        pass


class VGScientaDetector(
    AbstractElectronAnalyserDetector[
        VGScientaAnalyserDriverIO, VGScientaSequence, VGScientaRegion
    ]
):
    def __init__(self, prefix: str, name: str):
        super().__init__(prefix, name, VGScientaSequence)

    def _create_driver(self, prefix: str) -> VGScientaAnalyserDriverIO:
        return VGScientaAnalyserDriverIO(prefix, "driver")

    def _create_region_detector(
        self, driver: VGScientaAnalyserDriverIO, region: VGScientaRegion
    ) -> VGScientaRegionDetector:
        return VGScientaRegionDetector(self.name, driver, region)
