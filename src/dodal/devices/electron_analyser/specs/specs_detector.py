from typing import Generic

from dodal.devices.electron_analyser.base.base_controller import (
    ElectronAnalyserController,
)
from dodal.devices.electron_analyser.base.base_detector import ElectronAnalyserDetector
from dodal.devices.electron_analyser.base.base_region import TLensMode, TPsuMode
from dodal.devices.electron_analyser.base.energy_sources import AbstractEnergySource
from dodal.devices.electron_analyser.specs.specs_driver_io import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.specs.specs_region import SpecsRegion
from dodal.devices.fast_shutter import FastShutter
from dodal.devices.selectable_source import SourceSelector


class SpecsDetector(
    ElectronAnalyserDetector[
        SpecsAnalyserDriverIO[TLensMode, TPsuMode],
        SpecsRegion[TLensMode, TPsuMode],
    ],
    Generic[TLensMode, TPsuMode],
):
    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        energy_source: AbstractEnergySource,
        shutter: FastShutter | None = None,
        source_selector: SourceSelector | None = None,
        name: str = "",
    ):
        driver = SpecsAnalyserDriverIO[TLensMode, TPsuMode](
            prefix, lens_mode_type, psu_mode_type
        )
        controller = ElectronAnalyserController[
            SpecsAnalyserDriverIO[TLensMode, TPsuMode], SpecsRegion[TLensMode, TPsuMode]
        ](driver, energy_source, shutter, source_selector)

        super().__init__(controller, name)
