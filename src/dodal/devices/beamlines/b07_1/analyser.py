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

B07CSpecsRegion = SpecsRegion[LensMode, PsuMode]
B07CSpecsSequence = SpecsSequence[LensMode, PsuMode]


class B07CSpecsAnalyserDriverIO(SpecsAnalyserDriverIO):
    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix, LensMode, PsuMode, name)


B07CElectronAnalyserController = ElectronAnalyserController[
    B07CSpecsAnalyserDriverIO, B07CSpecsRegion
]


class B07CSpecs150(
    ElectronAnalyserDetector[B07CSpecsAnalyserDriverIO, B07CSpecsRegion]
):
    def __init__(
        self,
        prefix: str,
        energy_source: EnergySource,
        shutter: FastShutter | None = None,
        name: str = "",
    ):
        controller = B07CElectronAnalyserController(
            B07CSpecsAnalyserDriverIO(prefix), energy_source, shutter
        )
        super().__init__(controller, name)
