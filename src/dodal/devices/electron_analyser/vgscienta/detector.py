from collections.abc import Mapping
from typing import Generic

from ophyd_async.core import SignalR

from dodal.devices.electron_analyser.abstract.base_region import TLensMode
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
        VGScientaAnalyserDriverIO[TLensMode],
        VGScientaSequence[TLensMode],
        VGScientaRegion[TLensMode],
    ],
    Generic[TLensMode],
):
    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        energy_sources: Mapping[str, SignalR[float]],
        name: str = "",
    ):
        driver = VGScientaAnalyserDriverIO[TLensMode](
            prefix, lens_mode_type, energy_sources
        )
        seq = VGScientaSequence[lens_mode_type]
        super().__init__(seq, driver, name)
