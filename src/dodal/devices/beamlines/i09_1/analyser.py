from dodal.devices.beamlines.i09_1.enums import LensMode, PsuMode
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

I091SpecsRegion = SpecsRegion[LensMode, PsuMode]
I091SpecsSequence = SpecsSequence[LensMode, PsuMode]


class I091SpecsAnalyserDriverIO(SpecsAnalyserDriverIO):
    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix, LensMode, PsuMode, name)


I091ElectronAnalyserController = ElectronAnalyserController[
    I091SpecsAnalyserDriverIO, I091SpecsRegion
]


class SpecsPhoibos225(
    ElectronAnalyserDetector[I091SpecsAnalyserDriverIO, I091SpecsRegion]
):
    def __init__(
        self,
        prefix: str,
        energy_source: EnergySource,
        shutter: FastShutter | None = None,
        name: str = "",
    ):
        drv = I091SpecsAnalyserDriverIO(prefix)
        controller = I091ElectronAnalyserController(drv, energy_source, shutter)
        super().__init__(controller, name)
