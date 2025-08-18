from typing import Generic, TypeVar

from bluesky.protocols import Stageable
from ophyd_async.core import (
    AsyncStatus,
    Reference,
)

from dodal.common.data_util import load_json_file_to_class
from dodal.devices.electron_analyser.abstract.base_detector import (
    AbstractElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.abstract.base_driver_io import (
    TAbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.abstract.base_region import (
    TAbstractBaseRegion,
    TAbstractBaseSequence,
)


class ElectronAnalyserRegionDetector(
    AbstractElectronAnalyserDetector[TAbstractAnalyserDriverIO],
    Generic[TAbstractAnalyserDriverIO, TAbstractBaseRegion],
):
    """
    Extends electron analyser detector to configure specific region settings before data
    acqusition. This object must be passed in a driver and store it as a reference. It
    is designed to only exist inside a plan.
    """

    def __init__(
        self,
        driver: TAbstractAnalyserDriverIO,
        region: TAbstractBaseRegion,
        name: str = "",
    ):
        self._driver_ref = Reference(driver)
        self.region = region
        super().__init__(driver, name)

    @property
    def driver(self) -> TAbstractAnalyserDriverIO:
        # Store as a reference, this implementation will be given a driver so needs to
        # make sure we don't get conflicting parents.
        return self._driver_ref()

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        # Configure region parameters on the driver first before data collection.
        await self.driver.set(self.region)
        await super().trigger()


TElectronAnalyserRegionDetector = TypeVar(
    "TElectronAnalyserRegionDetector",
    bound=ElectronAnalyserRegionDetector,
)


class ElectronAnalyserDetector(
    AbstractElectronAnalyserDetector[TAbstractAnalyserDriverIO],
    Stageable,
    Generic[
        TAbstractAnalyserDriverIO,
        TAbstractBaseSequence,
        TAbstractBaseRegion,
    ],
):
    """
    Electron analyser detector with the additional functionality to load a sequence file
    and create a list of temporary ElectronAnalyserRegionDetector objects. These will
    setup configured region settings before data acquisition.
    """

    def __init__(
        self,
        sequence_class: type[TAbstractBaseSequence],
        driver: TAbstractAnalyserDriverIO,
        name: str = "",
    ):
        # Pass in driver
        self._driver = driver
        self._sequence_class = sequence_class
        super().__init__(self.driver, name)

    @property
    def driver(self) -> TAbstractAnalyserDriverIO:
        # This implementation creates the driver and wants this to be the parent so it
        # can be used with connect() method.
        return self._driver

    @AsyncStatus.wrap
    async def stage(self) -> None:
        """
        Prepare the detector for use by ensuring it is idle and ready.

        This method asynchronously stages the detector by first disarming the controller
        to ensure the detector is not actively acquiring data, then invokes the driver's
        stage procedure. This ensures the detector is in a known, ready state
        before use.

        Raises:
            Any exceptions raised by the driver's stage or controller's disarm methods.
        """
        await self.controller.disarm()
        await self.driver.stage()

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        """Disarm the detector."""
        await self.controller.disarm()
        await self.driver.unstage()

    def load_sequence(self, filename: str) -> TAbstractBaseSequence:
        """
        Load the sequence data from a provided json file into a sequence class.

        Args:
            filename: Path to the sequence file containing the region data.

        Returns:
            Pydantic model representing the sequence file.
        """
        return load_json_file_to_class(self._sequence_class, filename)

    def create_region_detector_list(
        self, filename: str, enabled_only=True
    ) -> list[
        ElectronAnalyserRegionDetector[TAbstractAnalyserDriverIO, TAbstractBaseRegion]
    ]:
        """
        Create a list of detectors equal to the number of regions in a sequence file.
        Each detector is responsible for setting up a specific region.

        Args:
            filename:     Path to the sequence file containing the region data.
            enabled_only: If true, only include the region if enabled is True.

        Returns:
            List of ElectronAnalyserRegionDetector, equal to the number of regions in
            the sequence file.
        """
        seq = self.load_sequence(filename)
        regions = seq.get_enabled_regions() if enabled_only else seq.regions
        return [
            ElectronAnalyserRegionDetector(self.driver, r, self.name + "_" + r.name)
            for r in regions
        ]


TElectronAnalyserDetector = TypeVar(
    "TElectronAnalyserDetector",
    bound=ElectronAnalyserDetector,
)
