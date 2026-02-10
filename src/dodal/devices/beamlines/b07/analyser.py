from dodal.devices.beamlines.b07.enums import LensMode
from dodal.devices.beamlines.b07_shared.enums import PsuMode
from dodal.devices.electron_analyser.base.base_controller import (
    ElectronAnalyserController,
)
from dodal.devices.electron_analyser.base.base_detector import ElectronAnalyserDetector
from dodal.devices.electron_analyser.base.energy_sources import EnergySource
from dodal.devices.electron_analyser.specs import (
    SpecsAnalyserDriverIO,
    SpecsRegion,
    SpecsSequence,
)
from dodal.devices.fast_shutter import FastShutter

B07SpecsRegion = SpecsRegion[LensMode, PsuMode]
B07SpecsSequence = SpecsSequence[LensMode, PsuMode]


class B07SpecsAnalyserDriverIO(SpecsAnalyserDriverIO):
    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix, LensMode, PsuMode, name)


B07ElectronAnalyserController = ElectronAnalyserController[
    B07SpecsAnalyserDriverIO, B07SpecsRegion
]


class Specs2DCMOS(ElectronAnalyserDetector[B07SpecsAnalyserDriverIO, B07SpecsRegion]):
    def __init__(
        self,
        prefix: str,
        energy_source: EnergySource,
        shutter: FastShutter | None = None,
        name: str = "",
    ):
        drv = B07SpecsAnalyserDriverIO(prefix)
        controller = B07ElectronAnalyserController(drv, energy_source, shutter)
        super().__init__(controller, name)
