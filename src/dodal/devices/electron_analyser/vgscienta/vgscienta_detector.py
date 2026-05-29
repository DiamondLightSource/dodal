from typing import Generic

from ophyd_async.core import SignalR, soft_signal_rw
from ophyd_async.epics.adcore import ADAcquireLogic

from dodal.devices.electron_analyser.base.base_detector import ElectronAnalyserDetector
from dodal.devices.electron_analyser.base.base_region import (
    TLensMode,
    TPassEnergy,
    TPsuMode,
)
from dodal.devices.electron_analyser.base.detector_logic import (
    ElectronAnalayserTriggerLogic,
    RegionLogic,
    ShutterCoordinatorADAcquireLogic,
)
from dodal.devices.electron_analyser.vgscienta.vgscienta_driver_io import (
    VGScientaAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta.vgscienta_region import VGScientaRegion
from dodal.devices.fast_shutter import GenericFastShutter
from dodal.devices.selectable_source import SourceSelector


class VGScientaDetector(
    ElectronAnalyserDetector[
        VGScientaAnalyserDriverIO[TLensMode, TPsuMode, TPassEnergy],
        VGScientaRegion[TLensMode, TPassEnergy],
    ],
    Generic[TLensMode, TPsuMode, TPassEnergy],
):
    def __init__(
        self,
        prefix: str,
        lens_mode_type: type[TLensMode],
        psu_mode_type: type[TPsuMode],
        pass_energy_type: type[TPassEnergy],
        energy_source: SignalR[float],
        shutter: GenericFastShutter | None = None,
        source_selector: SourceSelector | None = None,
        name: str = "",
    ):
        # Make attribute of class so connect applies to driver and populates parent.
        self.driver = VGScientaAnalyserDriverIO[TLensMode, TPsuMode, TPassEnergy](
            prefix, lens_mode_type, psu_mode_type, pass_energy_type
        )
        region_logic = RegionLogic(self.driver, energy_source, source_selector)
        self.close_shutter_idle = soft_signal_rw(bool, initial_value=True)
        acquire_logic = (
            ShutterCoordinatorADAcquireLogic(
                self.driver, shutter, self.close_shutter_idle
            )
            if shutter is not None
            else ADAcquireLogic(self.driver)
        )
        trigger_logic = ElectronAnalayserTriggerLogic(self.driver, set())
        config_sigs = (
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
        )
        super().__init__(
            region_logic=region_logic,
            acquire_logic=acquire_logic,
            trigger_logic=trigger_logic,
            config_sigs=config_sigs,
            name=name,
        )
