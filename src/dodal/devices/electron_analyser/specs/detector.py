from collections.abc import Mapping

from ophyd_async.core import SignalR

from dodal.devices.electron_analyser.detector import (
    ElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.specs.driver_io import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.specs.region import SpecsRegion, SpecsSequence


class SpecsDetector(
    ElectronAnalyserDetector[SpecsAnalyserDriverIO, SpecsSequence, SpecsRegion]
):
    def __init__(
        self, prefix: str, energy_sources: Mapping[str, SignalR[float]], name: str = ""
    ):
        driver = SpecsAnalyserDriverIO(prefix, energy_sources)
        super().__init__(SpecsSequence, driver, name)
