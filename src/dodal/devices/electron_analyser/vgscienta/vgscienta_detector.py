from typing import Generic

from dodal.devices.electron_analyser.base.base_controller import (
    ElectronAnalyserController,
)
from dodal.devices.electron_analyser.base.base_detector import ElectronAnalyserDetector
from dodal.devices.electron_analyser.base.base_region import TLensMode, TPsuMode
from dodal.devices.electron_analyser.base.energy_sources import AbstractEnergySource
from dodal.devices.electron_analyser.vgscienta.vgscienta_driver_io import (
    VGScientaAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta.vgscienta_region import (
    TPassEnergyEnum,
    VGScientaRegion,
    VGScientaSequence,
)
from dodal.devices.fast_shutter import FastShutter
from dodal.devices.selectable_source import SourceSelector


class VGScientaDetector(
    ElectronAnalyserDetector[
        VGScientaSequence[TLensMode, TPsuMode, TPassEnergyEnum],
        VGScientaAnalyserDriverIO[TLensMode, TPsuMode, TPassEnergyEnum],
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
        energy_source: AbstractEnergySource,
        shutter: FastShutter | None = None,
        source_selector: SourceSelector | None = None,
        name: str = "",
    ):
        # Save to class so takes part with connect()
        self.driver = VGScientaAnalyserDriverIO[TLensMode, TPsuMode, TPassEnergyEnum](
            prefix, lens_mode_type, psu_mode_type, pass_energy_type
        )

        controller = ElectronAnalyserController[
            VGScientaAnalyserDriverIO[TLensMode, TPsuMode, TPassEnergyEnum],
            VGScientaRegion[TLensMode, TPassEnergyEnum],
        ](self.driver, energy_source, shutter, source_selector)

        sequence_class = VGScientaSequence[
            lens_mode_type, psu_mode_type, pass_energy_type
        ]
        super().__init__(sequence_class, controller, name)
