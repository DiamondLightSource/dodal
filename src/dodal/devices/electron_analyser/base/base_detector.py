from typing import Generic, TypeVar

from bluesky.protocols import Movable, Reading, Stageable, Triggerable
from event_model import DataKey
from ophyd_async.core import (
    AsyncConfigurable,
    AsyncReadable,
    AsyncStatus,
    Device,
    TriggerInfo,
    soft_signal_rw,
)

from dodal.common.data_util import load_json_file_to_class
from dodal.devices.electron_analyser.base.base_controller import (
    ElectronAnalyserController,
)
from dodal.devices.electron_analyser.base.base_driver_io import (
    GenericAnalyserDriverIO,
    TAbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.base.base_region import (
    GenericRegion,
    GenericSequence,
    TAbstractBaseRegion,
    TAbstractBaseSequence,
)


class SequenceLoader(Device, Movable[str], Generic[TAbstractBaseSequence]):
    """
    Docstring for SequenceLoader

    :var Args: Description
    :var filename: Description
    :vartype filename: Path
    :var Returns: Description
    :var https: Description
    """

    def __init__(self, sequence_class: type[TAbstractBaseSequence], name):
        self.sequence_file = soft_signal_rw(str, initial_value="Not set")
        self._sequence_class = sequence_class

    @AsyncStatus.wrap
    async def set(self, filename: str) -> None:
        await self.sequence_file.set(filename)

    async def load_sequence(self) -> TAbstractBaseSequence:
        """
        Load the sequence data from a provided json file into a sequence class.

        Args:
            filename: Path to the sequence file containing the region data.

        Returns:
            Pydantic model representing the sequence file.
        """
        return load_json_file_to_class(
            self._sequence_class, await self.sequence_file.get_value()
        )


class ElectronAnalyserDetector(
    Device,
    Triggerable,
    AsyncReadable,
    AsyncConfigurable,
    Stageable,
    Movable,
    Generic[TAbstractBaseSequence, TAbstractAnalyserDriverIO, TAbstractBaseRegion],
):
    """
    Detector for data acquisition of electron analyser.

    If possible, this should be changed to inherit from a StandardDetector. Currently,
    StandardDetector forces you to use a file writer which doesn't apply here.
    See issue https://github.com/bluesky/ophyd-async/issues/888
    """

    def __init__(
        self,
        sequence_class: type[TAbstractBaseSequence],
        controller: ElectronAnalyserController[
            TAbstractAnalyserDriverIO, TAbstractBaseRegion
        ],
        name: str = "",
    ):
        self._controller = controller
        self._sequence_class = sequence_class

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
    GenericSequence, GenericAnalyserDriverIO, GenericRegion
]
TElectronAnalyserDetector = TypeVar(
    "TElectronAnalyserDetector",
    bound=ElectronAnalyserDetector,
)
