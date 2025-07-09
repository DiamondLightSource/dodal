from collections.abc import Mapping
from typing import Generic

from ophyd_async.core import SignalR

from dodal.devices.electron_analyser.abstract.base_driver_io import TLensMode
from dodal.devices.electron_analyser.detector import (
    ElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.specs.driver_io import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.specs.region import SpecsRegion, SpecsSequence


class SpecsDetector(
    ElectronAnalyserDetector[
        SpecsAnalyserDriverIO[TLensMode],
        SpecsSequence[TLensMode],
        SpecsRegion[TLensMode],
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
        driver = SpecsAnalyserDriverIO[TLensMode](
            prefix, lens_mode_type, energy_sources
        )
        seq = SpecsSequence[lens_mode_type]
        super().__init__(seq, driver, name)
