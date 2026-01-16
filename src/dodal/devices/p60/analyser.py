from dodal.devices.electron_analyser.base import AbstractEnergySource
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector
from dodal.devices.p60.enums import LensMode, PassEnergy, PsuMode


class R4000(VGScientaDetector[LensMode, PsuMode, PassEnergy]):
    def __init__(
        self,
        prefix: str,
        energy_source: AbstractEnergySource,
        name: str = "",
    ):
        super().__init__(
            prefix,
            LensMode,
            PsuMode,
            PassEnergy,
            energy_source,
            None,
            None,
            name,
        )
