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

B07BSpecsRegion = SpecsRegion[LensMode, PsuMode]
B07BSpecsSequence = SpecsSequence[LensMode, PsuMode]


class B07BSpecsAnalyserDriverIO(SpecsAnalyserDriverIO):
    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix, LensMode, PsuMode, name)


B07BElectronAnalyserController = ElectronAnalyserController[
    B07BSpecsAnalyserDriverIO, B07BSpecsRegion
]


class B07BSpecs150(
    ElectronAnalyserDetector[B07BSpecsAnalyserDriverIO, B07BSpecsRegion]
):
    def __init__(
        self,
        prefix: str,
        energy_source: EnergySource,
        shutter: FastShutter | None = None,
        name: str = "",
    ):
        controller = B07BElectronAnalyserController(
            B07BSpecsAnalyserDriverIO(prefix), energy_source, shutter
        )
        super().__init__(controller, name)
