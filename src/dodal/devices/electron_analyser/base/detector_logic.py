from typing import Any, Generic

from ophyd_async.core import (
    DetectorTriggerLogic,
    SignalDict,
    SignalR,
)
from ophyd_async.epics.adcore import ADArmLogic, ADImageMode

from dodal.devices.electron_analyser.base.base_driver_io import (
    AbstractAnalyserDriverIO,
    TAbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.base.base_region import TAbstractBaseRegion
from dodal.devices.electron_analyser.base.energy_sources import AbstractEnergySource
from dodal.devices.fast_shutter import GenericFastShutter
from dodal.devices.selectable_source import SourceSelector


class ShutterCoordinatorADArmLogic(ADArmLogic, Generic[TAbstractAnalyserDriverIO]):
    """Extends the arm logic to coordinate opening shutters before acqusition with
    optional configuration of when to close.
    """

    def __init__(
        self,
        driver: TAbstractAnalyserDriverIO,
        shutter: GenericFastShutter,
        close_shutter_idle: SignalR[bool] | None = None,
    ):
        self._shutter = shutter
        self._close_shutter_idle = close_shutter_idle
        super().__init__(driver)

    async def arm(self):
        # Open shutter before data collection
        await self._shutter.set(self._shutter.open_state)
        await super().arm()

    async def wait_for_idle(self):
        await super().wait_for_idle()
        # Optionally close shutters between regions
        if (
            self._close_shutter_idle is not None
            and await self._close_shutter_idle.get_value()
        ):
            await self._shutter.set(self._shutter.close_state)


class ElectronAnalayserTriggerLogic(
    DetectorTriggerLogic, Generic[TAbstractAnalyserDriverIO]
):
    """Simple trigger logic for electron analyser."""

    def __init__(
        self, driver: TAbstractAnalyserDriverIO, config_sigs: set[SignalR[Any]]
    ):
        self.driver = driver
        self._config_sigs = config_sigs

    def config_sigs(self) -> set[SignalR[Any]]:
        """Return the signals that should appear in read_configuration."""
        return self._config_sigs

    def get_deadtime(self, config_values: SignalDict) -> float:
        return 0.0

    async def prepare_internal(self, num: int, livetime: float, deadtime: float):
        # Only set image mode to single, num images and exposure is done with region.
        await self.driver.image_mode.set(ADImageMode.SINGLE)


class RegionLogic:
    """Logic for wrapping electron analyser driver to correctly set region data."""

    def __init__(
        self,
        driver: AbstractAnalyserDriverIO,
        energy_source: AbstractEnergySource,
        source_selector: SourceSelector | None = None,
    ):
        self.driver = driver
        self.energy_source = energy_source
        self.source_selector = source_selector

    async def setup_with_region(self, region: TAbstractBaseRegion) -> None:
        """Logic to correctly wrap the driver with a region."""
        if self.source_selector is not None:
            await self.source_selector.set(region.excitation_energy_source)

        excitation_energy = await self.energy_source.energy.get_value()
        epics_region = region.prepare_for_epics(excitation_energy)
        await self.driver.set(epics_region)
