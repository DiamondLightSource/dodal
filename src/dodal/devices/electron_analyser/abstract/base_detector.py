from typing import Generic

from bluesky.protocols import Reading, Triggerable
from event_model import DataKey
from ophyd_async.core import (
    AsyncConfigurable,
    AsyncReadable,
    AsyncStatus,
    Device,
)
from ophyd_async.epics.adcore import ADBaseController

from dodal.devices.electron_analyser.abstract.base_driver_io import (
    TAbstractAnalyserDriverIO,
)


class BaseElectronAnalyserDetector(
    Device,
    Triggerable,
    AsyncReadable,
    AsyncConfigurable,
    Generic[TAbstractAnalyserDriverIO],
):
    """
    Detector for data acquisition of electron analyser. Can only acquire using settings
    already configured for the device.

    If possible, this should be changed to inherit from a StandardDetector. Currently,
    StandardDetector forces you to use a file writer which doesn't apply here.
    See issue https://github.com/bluesky/ophyd-async/issues/888
    """

    def __init__(
        self,
        controller: ADBaseController[TAbstractAnalyserDriverIO],
        name: str = "",
    ):
        self._controller = controller
        super().__init__(name)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
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
