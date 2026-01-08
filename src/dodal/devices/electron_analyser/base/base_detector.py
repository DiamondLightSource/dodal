from typing import Generic, TypeVar

from bluesky.protocols import Movable, Reading, Stageable, Triggerable
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
    AbstractBaseSequence,
    GenericRegion,
    SequenceLoader,
    TAbstractBaseRegion,
)


class ElectronAnalyserDetector(
    Device,
    Triggerable,
    AsyncReadable,
    AsyncConfigurable,
    Stageable,
    Movable,
    Generic[TAbstractAnalyserDriverIO, TAbstractBaseRegion],
):
    """
    Detector for data acquisition of electron analyser.

    If possible, this should be changed to inherit from a StandardDetector. Currently,
    StandardDetector forces you to use a file writer which doesn't apply here.
    See issue https://github.com/bluesky/ophyd-async/issues/888
    """

    def __init__(
        self,
        controller: ElectronAnalyserController[
            TAbstractAnalyserDriverIO, TAbstractBaseRegion
        ],
        sequence_loader: SequenceLoader[AbstractBaseSequence[TAbstractBaseRegion]],
        name: str = "",
    ):
        self._controller = controller
        self.sequence_loader = sequence_loader

        super().__init__(name)

    @AsyncStatus.wrap
    async def stage(self) -> None:
        """Disarm the detector."""
        await self._controller.disarm()

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

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        """Disarm the detector."""
        await self._controller.disarm()


GenericElectronAnalyserDetector = ElectronAnalyserDetector[
    GenericAnalyserDriverIO, GenericRegion
]
TElectronAnalyserDetector = TypeVar(
    "TElectronAnalyserDetector",
    bound=ElectronAnalyserDetector,
)
