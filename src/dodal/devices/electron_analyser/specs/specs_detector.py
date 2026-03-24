from typing import Generic

from ophyd_async.core import soft_signal_rw

from dodal.devices.electron_analyser.base.base_detector import ElectronAnalyserDetector
from dodal.devices.electron_analyser.base.base_region import TLensMode, TPsuMode
from dodal.devices.electron_analyser.base.detector_logic import (
    ADArmLogic,
    ElectronAnalayserTriggerLogic,
    RegionLogic,
    ShutterCoordinatorADArmLogic,
)
from dodal.devices.electron_analyser.base.energy_sources import AbstractEnergySource
from dodal.devices.electron_analyser.specs.specs_driver_io import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.specs.specs_region import SpecsRegion
from dodal.devices.fast_shutter import GenericFastShutter
from dodal.devices.selectable_source import SourceSelector


class SpecsDetector(
    ElectronAnalyserDetector[
        SpecsAnalyserDriverIO[TLensMode, TPsuMode],
        SpecsRegion[TLensMode, TPsuMode],
    ],
    Generic[TLensMode, TPsuMode],
):
    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        energy_source: AbstractEnergySource,
        shutter: GenericFastShutter | None = None,
        source_selector: SourceSelector | None = None,
        name: str = "",
    ):
        # Make attribute of class so connect applies to driver and populates parent.
        self.driver = SpecsAnalyserDriverIO[TLensMode, TPsuMode](
            prefix, lens_mode_type, psu_mode_type
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
                self.driver.acquire_time,
                self.driver.iterations,
                self.driver.total_steps,
                self.driver.total_time,
                self.driver.energy_axis,
                self.driver.angle_axis,
                self.driver.snapshot_values,
                self.driver.psu_mode,
            },
        )

        super().__init__(
            region_logic=region_logic,
            arm_logic=arm_logic,
            trigger_logic=trigger_logic,
            name=name,
        )
