from typing import Generic

from ophyd_async.core import soft_signal_rw
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
        self.close_shutter_idle = soft_signal_rw(bool, initial_value=True)
        arm_logic = (
            ShutterCoordinatorADArmLogic(self.driver, shutter, self.close_shutter_idle)
            if shutter is not None
            else ADArmLogic(self.driver)
        )
        trigger_logic = ElectronAnalayserTriggerLogic(
            self.driver,
            {
                self.driver.region_name,
                self.driver.energy_mode,
                self.driver.acquisition_mode,
                self.driver.lens_mode,
                self.driver.low_energy,
                self.driver.centre_energy,
                self.driver.high_energy,
                self.driver.energy_step,
                self.driver.pass_energy,
                self.driver.slices,
                self.driver.iterations,
                self.driver.total_steps,
                self.driver.acquire_time,
                self.driver.total_time,
                self.driver.energy_axis,
                self.driver.angle_axis,
                self.driver.detector_mode,
                self.driver.region_min_x,
                self.driver.region_size_x,
                self.driver.sensor_max_size_x,
                self.driver.region_min_y,
                self.driver.region_size_y,
                self.driver.sensor_max_size_y,
                self.driver.psu_mode,
            },
        )

        super().__init__(
            region_logic=region_logic,
            arm_logic=arm_logic,
            trigger_logic=trigger_logic,
            name=name,
        )
