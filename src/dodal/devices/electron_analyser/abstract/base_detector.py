from collections.abc import Sequence
from typing import Generic

from bluesky.protocols import Reading, Triggerable
from event_model import DataKey
from ophyd_async.core import (
    AsyncConfigurable,
    AsyncReadable,
    AsyncStatus,
    Device,
    SignalR,
    merge_gathered_dicts,
)
from ophyd_async.epics.adcore import ADBaseController

from dodal.devices.electron_analyser.abstract.base_driver_io import (
    TAbstractAnalyserDriverIO,
)


class AbstractElectronAnalyserDetector(
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
        config_sigs: Sequence[SignalR] = (),
        name: str = "",
    ):
        self.controller = controller
        self._config_sigs = config_sigs
        super().__init__(name)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        await self.controller.arm()
        await self.controller.wait_for_idle()

    async def read(self) -> dict[str, Reading]:
        return await self.controller.driver.read()

    async def describe(self) -> dict[str, DataKey]:
        data = await self.controller.driver.describe()
        # Correct the shape for image
        driver = self.controller.driver
        energy_size = len(await driver.energy_axis.get_value())
        angle_size = len(await driver.angle_axis.get_value())
        prefix = driver.name + "-"
        data[prefix + "image"]["shape"] = [angle_size, energy_size]
        return data

    async def read_configuration(self) -> dict[str, Reading]:
        return await merge_gathered_dicts(sig.read() for sig in self._config_sigs)

    async def describe_configuration(self) -> dict[str, DataKey]:
        return await merge_gathered_dicts(sig.describe() for sig in self._config_sigs)
