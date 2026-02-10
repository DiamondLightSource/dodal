from dodal.devices.beamlines.p60.enums import LensMode, PassEnergy, PsuMode
from dodal.devices.electron_analyser.base import AbstractEnergySource
from dodal.devices.electron_analyser.base.base_controller import (
    ElectronAnalyserController,
)
from dodal.devices.electron_analyser.base.base_detector import ElectronAnalyserDetector
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaRegion,
    VGScientaSequence,
)
from dodal.devices.electron_analyser.vgscienta.vgscienta_driver_io import (
    VGScientaAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta.vgscienta_region import (
    VGScientaRegion,
    VGScientaSequence,
)

P60VGScientnaRegion = VGScientaRegion[LensMode, PassEnergy]
P60VGScientaSequence = VGScientaSequence[LensMode, PsuMode, PassEnergy]


class P60VGScientaAnalyserDriverIO(
    VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy]
):
    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix, LensMode, PsuMode, PassEnergy, "ELEMENT_SET", name)


P60ElectronAnalyserController = ElectronAnalyserController[
    P60VGScientaAnalyserDriverIO, P60VGScientnaRegion
]


class R4000(
    ElectronAnalyserDetector[P60VGScientaAnalyserDriverIO, P60VGScientnaRegion]
):
    """Lab specific analyser for P60 lab. It does not have any shutters connected so
    will be None for this implementation. The selected_source also cannot be dynamically
    changed between regions, so will also be None so regions cannot select.
    """

    def __init__(
        self,
        prefix: str,
        energy_source: AbstractEnergySource,
        name: str = "",
    ):
        drv = P60VGScientaAnalyserDriverIO(prefix)
        controller = P60ElectronAnalyserController(
            drv,
            energy_source=energy_source,
            shutter=None,
            source_selector=None,
        )
        super().__init__(controller, name)
