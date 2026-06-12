from dataclasses import dataclass, field
from typing import Any

from ophyd_async.core import DetectorTriggerLogic, SignalDict, SignalR
from ophyd_async.epics.adcore import ADAcquireLogic, ADImageMode

from dodal.devices.electron_analyser.base.base_driver_io import AbstractAnalyserDriverIO
from dodal.devices.electron_analyser.base.base_region import BaseRegion
from dodal.devices.fast_shutter import GenericFastShutter
from dodal.devices.selectable_source import SourceSelector


class ShutterCoordinatorADAcquireLogic(ADAcquireLogic):
    """Extends the acquire logic to coordinate opening shutters before acquisition with
    optional configuration of when to close.
    """

    def __init__(
        self,
        driver: AbstractAnalyserDriverIO,
        shutter: GenericFastShutter,
        close_shutter_when_idle: SignalR[bool] | None = None,
    ):
        self._shutter = shutter
        self._close_shutter_when_idle = close_shutter_when_idle
        super().__init__(driver)

    async def start_acquiring(self):
        # Open shutter before data collection
        await self._shutter.set(self._shutter.open_state)
        await super().start_acquiring()

    async def wait_for_idle(self):
        await super().wait_for_idle()
        # Optionally close shutters between regions
        if (
            self._close_shutter_when_idle is not None
            and await self._close_shutter_when_idle.get_value()
        ):
            await self._shutter.set(self._shutter.close_state)


@dataclass
class ElectronAnalayserTriggerLogic(DetectorTriggerLogic):
    """Simple trigger logic for electron analyser."""

    driver: AbstractAnalyserDriverIO
    config_signals: set[SignalR[Any]] = field(default_factory=set)
    deadtime: float = 0

    def config_sigs(self) -> set[SignalR[Any]]:
        """Return the signals that should appear in read_configuration."""
        return self.config_signals

    def get_deadtime(self, config_values: SignalDict) -> float:
        return self.deadtime

    async def prepare_internal(self, num: int, livetime: float, deadtime: float):
        # Only set image mode to single, num images and exposure is done with region logic.
        await self.driver.image_mode.set(ADImageMode.SINGLE)


@dataclass
class RegionLogic:
    """Logic for wrapping electron analyser driver to correctly set region data."""

    driver: AbstractAnalyserDriverIO
    energy_source: SignalR[float]
    source_selector: SourceSelector | None = None

    async def setup_with_region(self, region: BaseRegion) -> None:
        """Logic to correctly wrap the driver with a region."""
        if self.source_selector is not None:
            await self.source_selector.set(region.excitation_energy_source)

        excitation_energy = await self.energy_source.get_value()
        epics_region = region.prepare_for_epics(excitation_energy)
        await self.driver.set(epics_region)
