from typing import Generic, TypeVar

from ophyd_async.core import TriggerInfo
from ophyd_async.epics.adcore import ADImageMode

from dodal.devices.controllers import ConstantDeadTimeController
from dodal.devices.electron_analyser.base.base_driver_io import (
    GenericAnalyserDriverIO,
    TAbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.base.base_region import (
    GenericRegion,
    TAbstractBaseRegion,
)
from dodal.devices.electron_analyser.base.energy_sources import AbstractEnergySource
from dodal.devices.fast_shutter import FastShutter
from dodal.devices.selectable_source import SourceSelector


class ElectronAnalyserController(
    ConstantDeadTimeController[TAbstractAnalyserDriverIO],
    Generic[TAbstractAnalyserDriverIO, TAbstractBaseRegion],
):
    """
    Specialised controller for the electron analysers to provide additional setup logic
    such as selecting the energy source to use from requested region and giving the
    driver the correct region parameters.
    """

    def __init__(
        self,
        driver: TAbstractAnalyserDriverIO,
        energy_source: AbstractEnergySource,
        shutter: FastShutter | None = None,
        source_selector: SourceSelector | None = None,
        deadtime: float = 0,
        image_mode: ADImageMode = ADImageMode.SINGLE,
    ):
        """
        Parameters:
            driver: The electron analyser driver to wrap around that holds the PV's.
            energy_source: Device that holds the excitation energy and ability to switch
                           between sources.
            deadtime: For a given exposure, what is the safest minimum time between
                      exposures that can be determined without reading signals.
            image_mode: The image mode to configure the driver with before measuring.
        """
        self.energy_source = energy_source
        self.shutter = shutter
        self.source_selector = source_selector
        super().__init__(driver, deadtime, image_mode)

    async def setup_with_region(self, region: TAbstractBaseRegion) -> None:
        """Logic to set the driver with a region."""
        if self.source_selector is not None:
            await self.source_selector.set(region.excitation_energy_source)

        # Should this be moved to a VGScientController only?
        if self.shutter is not None:
            await self.shutter.set(self.shutter.close_state)

        excitation_energy = await self.energy_source.energy.get_value()
        epics_region = region.prepare_for_epics(excitation_energy)
        await self.driver.set(epics_region)

    async def prepare(self, trigger_info: TriggerInfo) -> None:
        """Do all necessary steps to prepare the detector for triggers."""
        # Let the driver know the excitation energy before measuring for binding energy
        # axis calculation.
        excitation_energy = await self.energy_source.energy.get_value()
        await self.driver.cached_excitation_energy.set(excitation_energy)

        if self.shutter is not None:
            await self.shutter.set(self.shutter.open_state)

        await super().prepare(trigger_info)


GenericElectronAnalyserController = ElectronAnalyserController[
    GenericAnalyserDriverIO, GenericRegion
]
TElectronAnalyserController = TypeVar(
    "TElectronAnalyserController", bound=ElectronAnalyserController
)
