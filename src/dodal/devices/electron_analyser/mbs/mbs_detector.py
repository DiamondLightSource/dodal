from collections.abc import Mapping, Sequence
from typing import Generic

from ophyd_async.core import SignalR
from ophyd_async.epics.adcore import ADAcquireLogic, ADWriterFactory, NDPluginBaseIO

from dodal.devices.electron_analyser.base import ElectronAnalyserDetector
from dodal.devices.electron_analyser.base.base_detector import ElectronAnalyserDetector
from dodal.devices.electron_analyser.base.base_region import TLensMode, TPassEnergy
from dodal.devices.electron_analyser.base.detector_logic import (
    ElectronAnalayserTriggerLogic,
    RegionLogic,
)
from dodal.devices.electron_analyser.mbs.mbs_driver_io import MbsAnalyserDriverIO
from dodal.devices.electron_analyser.mbs.mbs_region import MbsRegion


class MbsDetector(
    ElectronAnalyserDetector[
        MbsAnalyserDriverIO[TLensMode, TPassEnergy], MbsRegion[TLensMode, TPassEnergy]
    ],
    Generic[TLensMode, TPassEnergy],
):
    def __init__(
        self,
        prefix: str,
        driver: MbsAnalyserDriverIO[TLensMode, TPassEnergy],
        *writer_factories: ADWriterFactory,
        acquire_logic: ADAcquireLogic,
        trigger_logic: ElectronAnalayserTriggerLogic,
        region_logic: RegionLogic,
        plugins: Mapping[str, NDPluginBaseIO] | None = None,
        config_sigs: Sequence[SignalR] = (),
        name: str = "",
    ):
        config_sigs = (
            *config_sigs,
            driver.region_name,
            driver.energy_mode,
            driver.acquisition_mode,
            driver.lens_mode,
            driver.low_energy,
            driver.centre_energy,
            driver.high_energy,
            driver.deflector_x,
            driver.energy_step,
            driver.pass_energy,
            driver.slices,
            driver.iterations,
            driver.total_steps,
            driver.acquire_time,
            driver.acquire_period,
            driver.total_time,
            driver.energy_axis,
            driver.angle_axis,
            driver.psu_mode,
            driver.dither_steps,
            driver.spin_offset,
            driver.array_size_x,
            driver.array_size_y,
            driver.min_x,
            driver.min_y,
            driver.max_x,
            driver.max_y,
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
