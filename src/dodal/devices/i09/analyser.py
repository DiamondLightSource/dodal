from dodal.devices.electron_analyser.base import AbstractEnergySource
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector
from dodal.devices.fast_shutter import FastShutter
from dodal.devices.i09.enums import LensMode, PassEnergy, PsuMode
from dodal.devices.selectable_source import SourceSelector


class EW4000(VGScientaDetector[LensMode, PsuMode, PassEnergy]):
    def __init__(
        self,
        prefix: str,
        energy_source: AbstractEnergySource,
        shutter: FastShutter | None = None,
        source_selector: SourceSelector | None = None,
        name: str = "",
    ):
        super().__init__(
            prefix,
            LensMode,
            PsuMode,
            PassEnergy,
            energy_source,
            shutter,
            source_selector,
            name,
        )
