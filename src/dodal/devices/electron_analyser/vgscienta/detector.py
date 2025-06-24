from collections.abc import Mapping

from ophyd_async.core import SignalR

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
    def __init__(
        self, prefix: str, energy_sources: Mapping[str, SignalR], name: str = ""
    ):
        driver = VGScientaAnalyserDriverIO(prefix, energy_sources)
        super().__init__(VGScientaSequence, driver, name)
