from typing import Generic

from dodal.devices.electron_analyser.common.energy_sources import (
    DualEnergySource,
    EnergySource,
)
from dodal.devices.electron_analyser.detector.base_detector import (
    ElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.driver_io.base_driver_io import TPsuMode
from dodal.devices.electron_analyser.driver_io.specs_driver_io import (
    SpecsAnalyserDriverIO,
)
from dodal.devices.electron_analyser.region.base_region import TLensMode
from dodal.devices.electron_analyser.region.specs_region import (
    SpecsRegion,
    SpecsSequence,
)


class SpecsDetector(
    ElectronAnalyserDetector[
        SpecsAnalyserDriverIO[TLensMode, TPsuMode],
        SpecsSequence[TLensMode, TPsuMode],
        SpecsRegion[TLensMode, TPsuMode],
    ],
    Generic[TLensMode, TPsuMode],
):
    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        energy_source: DualEnergySource | EnergySource,
        name: str = "",
    ):
        driver = SpecsAnalyserDriverIO[TLensMode, TPsuMode](
            prefix, lens_mode_type, psu_mode_type, energy_source
        )
        super().__init__(SpecsSequence[lens_mode_type, psu_mode_type], driver, name)
