from typing import Generic

from ophyd_async.core import TriggerInfo
from ophyd_async.epics.adcore import ADImageMode

from dodal.devices.controllers import ConstantDeadTimeController
from dodal.devices.electron_analyser.abstract.base_driver_io import (
    TAbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.abstract.base_region import TAbstractBaseRegion
from dodal.devices.electron_analyser.energy_sources import (
    AbstractEnergySource,
    DualEnergySource,
)


class ElectronAnalyserController(
    ConstantDeadTimeController[TAbstractAnalyserDriverIO],
    Generic[TAbstractAnalyserDriverIO, TAbstractBaseRegion],
):
    def __init__(
        self,
        driver: TAbstractAnalyserDriverIO,
        energy_source: AbstractEnergySource,
        deadtime: float,
        image_mode: ADImageMode = ADImageMode.SINGLE,
    ):
        self.energy_source = energy_source
        super().__init__(driver, deadtime, image_mode)

    async def setup_with_region(self, region: TAbstractBaseRegion):
        if isinstance(self.energy_source, DualEnergySource):
            self.energy_source.selected_source.set(region.excitation_energy_source)
        excitation_energy = await self.energy_source.energy.get_value()
        epics_region = region.prepare_for_epics(excitation_energy)
        await self.driver.set(epics_region)

    async def prepare(self, trigger_info: TriggerInfo) -> None:
        # Let the driver know the excitation energy for binding energy axis
        excitation_energy = await self.energy_source.energy.get_value()
        await self.driver.cached_excitation_energy.set(excitation_energy)
        await super().prepare(trigger_info)
