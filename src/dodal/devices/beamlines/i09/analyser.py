from dodal.devices.beamlines.i09.enums import LensMode, PassEnergy, PsuMode
from dodal.devices.electron_analyser.base import DualEnergySource
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
from dodal.devices.fast_shutter import DualFastShutter
from dodal.devices.selectable_source import SourceSelector

I09VGScientaRegion = VGScientaRegion[LensMode, PassEnergy]
I09VGScientaSequence = VGScientaSequence[LensMode, PsuMode, PassEnergy]


class I09VGScientaAnalyserDriverIO(
    VGScientaAnalyserDriverIO[LensMode, PsuMode, PassEnergy]
):
    def __init__(self, prefix: str, name: str = ""):
        super().__init__(prefix, LensMode, PsuMode, PassEnergy, "ELEMENT_SET", name)


I09ElectronAnalyserController = ElectronAnalyserController[
    I09VGScientaAnalyserDriverIO, I09VGScientaRegion
]


class EW4000(
    ElectronAnalyserDetector[I09VGScientaAnalyserDriverIO, I09VGScientaRegion]
):
    """Implementation of VGScienta Electron Analyser. This model is unique for i09
    beamline because it has access to multiple energy sources and shutters. The selected
    source is deterimined by the source_selector device.
    """

    def __init__(
        self,
        prefix: str,
        dual_energy_source: DualEnergySource,
        dual_fast_shutter: DualFastShutter,
        source_selector: SourceSelector,
        name: str = "",
    ):
        drv = I09VGScientaAnalyserDriverIO(prefix)
        controller = I09ElectronAnalyserController(
            drv, dual_energy_source, dual_fast_shutter, source_selector
        )
        super().__init__(controller, name)
