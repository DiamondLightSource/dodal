from typing import Generic

from ophyd_async.epics.adcore import ADArmLogic

from dodal.devices.electron_analyser.base.base_detector import ElectronAnalyserDetector
from dodal.devices.electron_analyser.base.base_region import TLensMode, TPsuMode
from dodal.devices.electron_analyser.base.detector_logic import (
    ADArmLogic,
    ElectronAnalayserTriggerLogic,
    RegionLogic,
    ShutterCoordinatorADArmLogic,
)
from dodal.devices.electron_analyser.base.energy_sources import AbstractEnergySource
from dodal.devices.electron_analyser.vgscienta.vgscienta_driver_io import (
    VGScientaAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta.vgscienta_region import (
    TPassEnergyEnum,
    VGScientaRegion,
)
from dodal.devices.fast_shutter import FastShutter
from dodal.devices.selectable_source import SourceSelector


class VGScientaDetector(
    ElectronAnalyserDetector[
        VGScientaAnalyserDriverIO[TLensMode, TPsuMode, TPassEnergyEnum],
        VGScientaRegion[TLensMode, TPassEnergyEnum],
    ],
    Generic[TLensMode, TPsuMode, TPassEnergyEnum],
):
    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        pass_energy_type: type[TPassEnergyEnum],
        energy_source: AbstractEnergySource,
        shutter: FastShutter | None = None,
        source_selector: SourceSelector | None = None,
        name: str = "",
    ):
        # Make attribute of class so connect applies to driver and populates parent.
        self.driver = VGScientaAnalyserDriverIO[TLensMode, TPsuMode, TPassEnergyEnum](
            prefix, lens_mode_type, psu_mode_type, pass_energy_type
        )
        region_logic = RegionLogic(self.driver, energy_source, source_selector)
        arm_logic = (
            ShutterCoordinatorADArmLogic(self.driver, shutter)
            if shutter is not None
            else ADArmLogic(self.driver)
        )
        trigger_logic = ElectronAnalayserTriggerLogic(
            self.driver, {self.driver.lens_mode, self.driver.pass_energy}
        )

        super().__init__(
            region_logic=region_logic,
            arm_logic=arm_logic,
            trigger_logic=trigger_logic,
            name=name,
        )
