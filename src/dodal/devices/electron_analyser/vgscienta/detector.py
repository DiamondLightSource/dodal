from collections.abc import Mapping
from typing import Generic

from ophyd_async.core import SignalR

from dodal.devices.electron_analyser.abstract.base_region import TLensMode, TPsuMode
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
        VGScientaAnalyserDriverIO[TLensMode, TPsuMode],
        VGScientaSequence[TLensMode, TPsuMode],
        VGScientaRegion[TLensMode],
    ],
    Generic[TLensMode, TPsuMode],
):
    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        energy_sources: Mapping[str, SignalR[float]],
        name: str = "",
    ):
        driver = VGScientaAnalyserDriverIO[TLensMode, TPsuMode](
            prefix, lens_mode_type, psu_mode_type, energy_sources
        )
        super().__init__(VGScientaSequence[lens_mode_type, psu_mode_type], driver, name)
