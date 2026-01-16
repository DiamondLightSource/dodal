from dodal.devices.b07.enums import LensMode
from dodal.devices.b07_shared.enums import PsuMode
from dodal.devices.electron_analyser.base.energy_sources import EnergySource
from dodal.devices.electron_analyser.specs import SpecsDetector
from dodal.devices.fast_shutter import FastShutter


class Specs2DCMOS(SpecsDetector[LensMode, PsuMode]):
    def __init__(
        self,
        prefix: str,
        energy_source: EnergySource,
        shutter: FastShutter | None = None,
        name: str = "",
    ):
        super().__init__(prefix, LensMode, PsuMode, energy_source, shutter, None, name)
