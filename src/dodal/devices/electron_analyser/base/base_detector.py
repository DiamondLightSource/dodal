from typing import Generic

from ophyd_async.core import (
    AsyncStatus,
    DetectorArmLogic,
    DetectorTriggerLogic,
    StandardDetector,
    error_if_none,
)

from dodal.devices.electron_analyser.base.base_driver_io import (
    GenericAnalyserDriverIO,
    TAbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.base.base_region import (
    GenericRegion,
    TAbstractBaseRegion,
)
from dodal.devices.electron_analyser.base.detector_logic import RegionLogic


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
        """Configure detector with regions from plans."""
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


GenericElectronAnalyserDetector = ElectronAnalyserDetector[
    GenericAnalyserDriverIO, GenericRegion
]
