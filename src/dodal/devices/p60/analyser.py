from dodal.devices.electron_analyser.base import AbstractEnergySource
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector
from dodal.devices.p60.enums import LensMode, PassEnergy, PsuMode


class R4000(VGScientaDetector[LensMode, PsuMode, PassEnergy]):
    """Lab specific analyser for P60 lab. It does not have any shutters connected so
    will be None for this implementation. The selected_source also cannot be dynamically
    changed between regions, so will also be None so regions cannot select."""

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
