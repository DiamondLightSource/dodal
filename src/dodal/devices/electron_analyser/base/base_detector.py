import asyncio
from typing import Generic, TypeVar

from bluesky.protocols import Preparable, Reading, Stageable, Triggerable
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
    AbstractBaseRegion,
    AbstractBaseSequence,
    GenericRegion,
    TAbstractBaseRegion,
)


class SequenceHolder(Stageable, Preparable):
    """Wrapper to hold the sequence data for an electron analyser.

    Used in scans when we need to hold the state of the configured sequence of regions
    to give to the electron analyser for each step of a scan.
    """

    def __init__(self):
        self.data: AbstractBaseSequence[AbstractBaseRegion] | None = None

    @AsyncStatus.wrap
    async def prepare(self, value: AbstractBaseSequence[AbstractBaseRegion] | None):
        self.data = value

    @AsyncStatus.wrap
    async def stage(self):
        pass

    @AsyncStatus.wrap
    async def unstage(self):
        self.data = None


class ElectronAnalyserDetector(
    Device,
    Stageable,
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
        self.sequence = SequenceHolder()
        self._controller = controller
        super().__init__(name)

    @AsyncStatus.wrap
    async def stage(self) -> None:
        """Prepare the detector for use by ensuring it is idle and ready.

        This method asynchronously stages the detector by disarming the controller to
        ensure the detector is not actively acquiring data.

        Raises:
            Any exceptions raised by the driver's stage or controller's disarm methods.
        """
        await asyncio.gather(self._controller.disarm(), self.sequence.stage())

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        """Disarm the detector."""
        await asyncio.gather(self._controller.disarm(), self.sequence.unstage())

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


GenericElectronAnalyserDetector = ElectronAnalyserDetector[
    GenericAnalyserDriverIO, GenericRegion
]
TElectronAnalyserDetector = TypeVar(
    "TElectronAnalyserDetector",
    bound=ElectronAnalyserDetector,
)
