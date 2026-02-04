from dodal.devices.beamlines.b07_1.enums import LensMode
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

B071SpecsRegion = SpecsRegion[LensMode, PsuMode]
B071SpecsSequence = SpecsSequence[LensMode, PsuMode]


class B071SpecsAnalyserDriverIO(SpecsAnalyserDriverIO):
    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix, LensMode, PsuMode, name)


B071ElectronAnalyserController = ElectronAnalyserController[
    B071SpecsAnalyserDriverIO, B071SpecsRegion
]


class SpecsPhoibos(
    ElectronAnalyserDetector[B071SpecsAnalyserDriverIO, B071SpecsRegion]
):
    def __init__(
        self,
        prefix: str,
        energy_source: EnergySource,
        shutter: FastShutter | None = None,
        name: str = "",
    ):
        driver = B071SpecsAnalyserDriverIO(prefix)
        controller = B071ElectronAnalyserController(driver, energy_source, shutter)
        super().__init__(controller, name)
