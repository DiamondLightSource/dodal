import asyncio
from abc import abstractmethod
from typing import Generic

from bluesky.protocols import Reading, Stageable, Triggerable
from event_model import DataKey
from ophyd_async.core import (
    AsyncConfigurable,
    AsyncReadable,
    AsyncStatus,
    Device,
)
from ophyd_async.epics.adcore import (
    ADBaseController,
)

from dodal.devices.electron_analyser.abstract.base_driver_io import (
    AbstractAnalyserDriverIO,
    TAbstractAnalyserDriverIO,
)


class ElectronAnalyserController(ADBaseController[AbstractAnalyserDriverIO]):
    def get_deadtime(self, exposure: float | None) -> float:
        return 0


class AbstractElectronAnalyserDetector(
    Device,
    Stageable,
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
        driver: TAbstractAnalyserDriverIO,
        name: str = "",
    ):
        self.controller: ElectronAnalyserController = ElectronAnalyserController(
            driver=driver
        )
        super().__init__(name)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        await self.controller.arm()
        await self.controller.wait_for_idle()

    @AsyncStatus.wrap
    async def stage(self) -> None:
        """Make sure the detector is idle and ready to be used."""
        await self.driver.stage()
        await asyncio.gather(self.controller.disarm())

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        """Disarm the detector."""
        await asyncio.gather(self.controller.disarm())

    async def read(self) -> dict[str, Reading]:
        return await self.driver.read()

    async def describe(self) -> dict[str, DataKey]:
        data = await self.driver.describe()
        # Correct the shape for image
        prefix = self.driver.name + "-"
        energy_size = len(await self.driver.energy_axis.get_value())
        angle_size = len(await self.driver.angle_axis.get_value())
        data[prefix + "image"]["shape"] = [angle_size, energy_size]
        return data

    async def read_configuration(self) -> dict[str, Reading]:
        return await self.driver.read_configuration()

    async def describe_configuration(self) -> dict[str, DataKey]:
        return await self.driver.describe_configuration()

    @property
    @abstractmethod
    def driver(self) -> TAbstractAnalyserDriverIO:
        """
        Define common property for all implementations to access the driver. Some
        implementations will store this as a reference so it doesn't have conflicting
        parents.

        Returns:
            instance of the driver.
        """
