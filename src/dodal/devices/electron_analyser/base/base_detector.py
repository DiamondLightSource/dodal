from typing import Generic, TypeVar

from bluesky.protocols import Reading, Stageable, Triggerable
from event_model import DataKey
from ophyd_async.core import (
    AsyncConfigurable,
    AsyncReadable,
    AsyncStatus,
    Device,
    TriggerInfo,
)

from dodal.devices.electron_analyser.base.base_controller import (
    ElectronAnalyserController,
)
from dodal.devices.electron_analyser.base.base_driver_io import (
    GenericAnalyserDriverIO,
    TAbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.base.base_region import (
    GenericRegion,
    TAbstractBaseRegion,
)


class BaseElectronAnalyserDetector(
    Device,
    Triggerable,
    AsyncReadable,
    AsyncConfigurable,
    Generic[TAbstractAnalyserDriverIO, TAbstractBaseRegion],
):
    """Detector for data acquisition of electron analyser. Can only acquire using
    settings already configured for the device.

    If possible, this should be changed to inherit from a StandardDetector. Currently,
    StandardDetector forces you to use a file writer which doesn't apply here.
    See issue https://github.com/bluesky/ophyd-async/issues/888
    """

    def __init__(
        self,
        controller: ElectronAnalyserController[
            TAbstractAnalyserDriverIO, TAbstractBaseRegion
        ],
        name: str = "",
    ):
        self._controller = controller
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, region: TAbstractBaseRegion) -> None:
        await self._controller.setup_with_region(region)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        await self._controller.prepare(TriggerInfo())
        await self._controller.arm()
        await self._controller.wait_for_idle()

    async def read(self) -> dict[str, Reading]:
        return await self._controller.driver.read()

    async def describe(self) -> dict[str, DataKey]:
        data = await self._controller.driver.describe()
        # Correct the shape for image
        prefix = self._controller.driver.name + "-"
        energy_size = len(await self._controller.driver.energy_axis.get_value())
        angle_size = len(await self._controller.driver.angle_axis.get_value())
        data[prefix + "image"]["shape"] = [angle_size, energy_size]
        return data

    async def read_configuration(self) -> dict[str, Reading]:
        return await self._controller.driver.read_configuration()

    async def describe_configuration(self) -> dict[str, DataKey]:
        return await self._controller.driver.describe_configuration()


GenericBaseElectronAnalyserDetector = BaseElectronAnalyserDetector[
    GenericAnalyserDriverIO, GenericRegion
]


class ElectronAnalyserRegionDetector(
    BaseElectronAnalyserDetector[TAbstractAnalyserDriverIO, TAbstractBaseRegion],
    Generic[TAbstractAnalyserDriverIO, TAbstractBaseRegion],
):
    """Extends electron analyser detector to configure specific region settings before
    data acquisition. It is designed to only exist inside a plan.
    """

    def __init__(
        self,
        controller: ElectronAnalyserController[
            TAbstractAnalyserDriverIO, TAbstractBaseRegion
        ],
        region: TAbstractBaseRegion,
        name: str = "",
    ):
        self.region = region
        super().__init__(controller, name)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        # Configure region parameters on the driver first before data collection.
        await self.set(self.region)
        await super().trigger()


# Used in sm-bluesky, but will hopefully be removed along with
# ElectronAnalyserRegionDetector in future. Blocked by:
# https://github.com/bluesky/bluesky/pull/1978
GenericElectronAnalyserRegionDetector = ElectronAnalyserRegionDetector[
    GenericAnalyserDriverIO, GenericRegion
]
TElectronAnalyserRegionDetector = TypeVar(
    "TElectronAnalyserRegionDetector",
    bound=ElectronAnalyserRegionDetector,
)


class ElectronAnalyserDetector(
    BaseElectronAnalyserDetector[TAbstractAnalyserDriverIO, TAbstractBaseRegion],
    Stageable,
    Generic[TAbstractAnalyserDriverIO, TAbstractBaseRegion],
):
    """Electron analyser detector with the additional functionality to load a sequence
    file and create a list of temporary ElectronAnalyserRegionDetector objects. These
    will setup configured region settings before data acquisition.
    """

    def __init__(
        self,
        controller: ElectronAnalyserController[
            TAbstractAnalyserDriverIO, TAbstractBaseRegion
        ],
        name: str = "",
    ):
        # Save on device so connect works and names it as child
        self.driver = controller.driver
        super().__init__(controller, name)

    @AsyncStatus.wrap
    async def stage(self) -> None:
        """Prepare the detector for use by ensuring it is idle and ready.

        This method asynchronously stages the detector by first disarming the controller
        to ensure the detector is not actively acquiring data, then invokes the driver's
        stage procedure. This ensures the detector is in a known, ready state
        before use.

        Raises:
            Any exceptions raised by the driver's stage or controller's disarm methods.
        """
        await self._controller.disarm()

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        """Disarm the detector."""
        await self._controller.disarm()

    def create_region_detector_list(
        self, regions: list[TAbstractBaseRegion]
    ) -> list[
        ElectronAnalyserRegionDetector[TAbstractAnalyserDriverIO, TAbstractBaseRegion]
    ]:
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
        return [
            ElectronAnalyserRegionDetector[
                TAbstractAnalyserDriverIO, TAbstractBaseRegion
            ](self._controller, r, self.name + "_" + r.name)
            for r in regions
        ]


GenericElectronAnalyserDetector = ElectronAnalyserDetector[
    GenericAnalyserDriverIO, GenericRegion
]
TElectronAnalyserDetector = TypeVar(
    "TElectronAnalyserDetector",
    bound=ElectronAnalyserDetector,
)
