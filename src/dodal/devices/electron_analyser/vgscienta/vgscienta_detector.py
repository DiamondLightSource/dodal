from typing import Generic

from dodal.devices.electron_analyser.base.base_controller import (
    ElectronAnalyserController,
)
from dodal.devices.electron_analyser.base.base_detector import ElectronAnalyserDetector
from dodal.devices.electron_analyser.base.base_region import TLensMode, TPsuMode
from dodal.devices.electron_analyser.base.energy_sources import (
    DualEnergySource,
    EnergySource,
)
from dodal.devices.electron_analyser.vgscienta.vgscienta_driver_io import (
    VGScientaAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta.vgscienta_region import (
    TPassEnergyEnum,
    VGScientaRegion,
    VGScientaSequence,
)


class VGScientaDetector(
    ElectronAnalyserDetector[
        ElectronAnalyserController[
            VGScientaAnalyserDriverIO[TLensMode, TPsuMode, TPassEnergyEnum],
            VGScientaRegion[TLensMode, TPassEnergyEnum],
        ],
        VGScientaSequence[TLensMode, TPsuMode, TPassEnergyEnum],
        VGScientaRegion[TLensMode, TPassEnergyEnum],
    ],
    Generic[TLensMode, TPsuMode, TPassEnergyEnum],
):
    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        pass_energy_type: type[TPassEnergyEnum],
        energy_source: DualEnergySource | EnergySource,
        name: str = "",
    ):
        # Save to class so takes part with connect()
        self.driver = VGScientaAnalyserDriverIO[TLensMode, TPsuMode, TPassEnergyEnum](
            prefix,
            lens_mode_type,
            psu_mode_type,
            pass_energy_type,
        )
        controller = ElectronAnalyserController[
            VGScientaAnalyserDriverIO[TLensMode, TPsuMode, TPassEnergyEnum],
            VGScientaRegion[TLensMode, TPassEnergyEnum],
        ](self.driver, energy_source, 0)

        super().__init__(
            VGScientaSequence[lens_mode_type, psu_mode_type, pass_energy_type],
            controller,
            name,
        )
