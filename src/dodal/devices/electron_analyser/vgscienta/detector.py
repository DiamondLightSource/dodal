from dodal.common.data_util import load_json_file_to_class
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
    def _create_driver(self, prefix: str) -> VGScientaAnalyserDriverIO:
        return VGScientaAnalyserDriverIO(prefix, "driver")

    def load_sequence(self, filename: str) -> VGScientaSequence:
        return load_json_file_to_class(VGScientaSequence, filename)

    def _create_region_detector(
        self, driver: VGScientaAnalyserDriverIO, region: VGScientaRegion
    ) -> VGScientaRegionDetector:
        return VGScientaRegionDetector(self.name, driver, region)
