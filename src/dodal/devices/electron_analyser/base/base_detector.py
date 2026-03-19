from typing import Any, Generic

from ophyd_async.core import (
    AsyncStatus,
    DetectorArmLogic,
    DetectorTriggerLogic,
    SignalDict,
    SignalR,
    StandardDetector,
    error_if_none,
)
from ophyd_async.epics.adcore import ADArmLogic, ADImageMode

from dodal.devices.electron_analyser.base import TAbstractAnalyserDriverIO
from dodal.devices.electron_analyser.base.base_driver_io import (
    AbstractAnalyserDriverIO,
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


async def _get_value(value: SignalR[bool] | bool) -> bool:
    return await value.get_value() if isinstance(value, SignalR) else value


class ShutterCoordinatorADArmLogic(ADArmLogic, Generic[TAbstractAnalyserDriverIO]):
    """Or we do this inside a plan?"""

    def __init__(
        self,
        driver: TAbstractAnalyserDriverIO,
        shutter: FastShutter,
        close_shutter_idle: SignalR[bool] | bool = True,
        close_shutter_disarm: SignalR[bool] | bool = True,
    ):
        self._shutter = shutter
        self._close_shutter_idle = close_shutter_idle
        self._close_shutter_disarm = close_shutter_disarm
        super().__init__(driver)

    async def arm(self):
        # Open shutter before data collection
        self._shutter.set(self._shutter.open_state)
        await super().arm()

    async def wait_for_idle(self):
        await super().wait_for_idle()
        # Optionally close shutters between regions
        if await _get_value(self._close_shutter_idle):
            self._shutter.set(self._shutter.close_state)

    async def disarm(self):
        await super().disarm()
        if await _get_value(self._close_shutter_disarm):
            self._shutter.set(self._shutter.close_state)


class ElectronAnalayserTriggerLogic(
    DetectorTriggerLogic, Generic[TAbstractAnalyserDriverIO]
):
    def __init__(
        self, driver: TAbstractAnalyserDriverIO, config_sigs: set[SignalR[Any]]
    ):
        self._driver = driver
        self._config_sigs = self._config_sigs

    def config_sigs(self) -> set[SignalR[Any]]:
        """Return the signals that should appear in read_configuration."""
        return self._config_sigs

    def get_deadtime(self, config_values: SignalDict) -> float:
        return 0.0

    async def prepare_internal(self, num: int, livetime: float, deadtime: float):
        # set image mode, anything else?
        await self._driver.image_mode.set(ADImageMode.SINGLE)


class RegionLogic:
    """Logic for wrapping electron analyser driver to correctly set region data."""

    def __init__(
        self,
        driver: AbstractAnalyserDriverIO,
        energy_source: AbstractEnergySource,
        source_selector: SourceSelector | None = None,
    ):
        self._driver = driver
        self._energy_source = energy_source
        self._source_selector = source_selector

    async def setup_with_region(self, region: TAbstractBaseRegion) -> None:
        """Logic to correctly wrap the driver with a region."""
        if self._source_selector is not None:
            await self._source_selector.set(region.excitation_energy_source)

        excitation_energy = await self._energy_source.energy.get_value()
        epics_region = region.prepare_for_epics(excitation_energy)
        await self._driver.set(epics_region)


class ElectronAnalyserDetector(
    StandardDetector,
    Generic[TAbstractAnalyserDriverIO, TAbstractBaseRegion],
):
    """Detector for data acquisition of electron analyser. Can only acquire using
    settings already configured for the device.
    """

    def __init__(
        self,
        arm_logic: DetectorArmLogic,
        trigger_logic: DetectorTriggerLogic,
        region_logic: RegionLogic,
        # ToDo - Add data logic
        name: str = "",
    ):
        self.add_detector_logics(arm_logic, trigger_logic)
        # Custom logic for handling regions configured from sequence files.
        self._region_logic = region_logic
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, region: TAbstractBaseRegion) -> None:
        """Method so detector can be configured with regions from plans."""
        await self._region_logic.setup_with_region(region)

    def create_region_detector_list(
        self, regions: list[TAbstractBaseRegion]
    ) -> list["ElectronAnalyserDetector"]:
        """This method can hopefully be dropped when this is merged and released.
        https://github.com/bluesky/bluesky/pull/1978.

        Create a list of detectors equal to the number of regions. Each detector is
        responsible for setting up a specific region.

        Args:
            regions: The list of regions to give to each region detector.

        Returns:
            List of ElectronAnalyserRegionDetector, equal to the number of regions in
            the sequence file.
        """
        arm_logic = error_if_none(self._arm_logic, "arm_logic cannot be None.")
        trigger_logic = error_if_none(
            self._trigger_logic, "trigger_logic cannot be None."
        )
        return [
            ElectronAnalyserDetector(
                arm_logic=arm_logic,
                trigger_logic=trigger_logic,
                region_logic=self._region_logic,
                name=self.name + "_" + r.name,
            )
            for r in regions
        ]


GenericBaseElectronAnalyserDetector = ElectronAnalyserDetector[
    GenericAnalyserDriverIO, GenericRegion
]
