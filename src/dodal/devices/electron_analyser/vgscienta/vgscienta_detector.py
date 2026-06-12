from collections.abc import Mapping, Sequence
from typing import Generic

from ophyd_async.core import SignalR
from ophyd_async.epics.adcore import ADAcquireLogic, ADWriterFactory, NDPluginBaseIO

from dodal.devices.electron_analyser.base.base_detector import ElectronAnalyserDetector
from dodal.devices.electron_analyser.base.base_region import (
    TLensMode,
    TPassEnergy,
    TPsuMode,
)
from dodal.devices.electron_analyser.base.detector_logic import (
    ElectronAnalayserTriggerLogic,
    RegionLogic,
)
from dodal.devices.electron_analyser.vgscienta.vgscienta_driver_io import (
    VGScientaAnalyserDriverIO,
)
from dodal.devices.electron_analyser.vgscienta.vgscienta_region import VGScientaRegion


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
        driver: VGScientaAnalyserDriverIO[TLensMode, TPsuMode, TPassEnergy],
        *writer_factories: ADWriterFactory,
        acquire_logic: ADAcquireLogic,
        trigger_logic: ElectronAnalayserTriggerLogic,
        region_logic: RegionLogic,
        plugins: Mapping[str, NDPluginBaseIO] | None = None,
        config_sigs: Sequence[SignalR] = (),
        name: str = "",
    ):
        config_sigs = (
            driver.region_name,
            driver.energy_mode,
            driver.acquisition_mode,
            driver.lens_mode,
            driver.low_energy,
            driver.centre_energy,
            driver.high_energy,
            driver.energy_step,
            driver.pass_energy,
            driver.slices,
            driver.iterations,
            driver.total_steps,
            driver.acquire_time,
            driver.total_time,
            driver.energy_axis,
            driver.angle_axis,
            driver.detector_mode,
            driver.region_min_x,
            driver.region_size_x,
            driver.sensor_max_size_x,
            driver.region_min_y,
            driver.region_size_y,
            driver.sensor_max_size_y,
            driver.psu_mode,
        )
        super().__init__(
            driver,
            prefix,
            *writer_factories,
            region_logic=region_logic,
            acquire_logic=acquire_logic,
            trigger_logic=trigger_logic,
            plugins=plugins,
            config_sigs=config_sigs,
            name=name,
        )
