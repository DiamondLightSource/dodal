import asyncio
from abc import abstractmethod
from typing import Generic, TypeVar

from bluesky.protocols import (
    Reading,
    Stageable,
    Triggerable,
)
from event_model import DataKey
from ophyd_async.core import (
    AsyncStatus,
    Device,
    Reference,
)
from ophyd_async.core._protocol import AsyncConfigurable, AsyncReadable
from ophyd_async.epics.adcore import (
    ADBaseController,
)

from dodal.common.data_util import load_json_file_to_class
from dodal.devices.electron_analyser.abstract.base_driver_io import (
    AbstractAnalyserDriverIO,
    TAbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.abstract.base_region import (
    TAbstractBaseRegion,
    TAbstractBaseSequence,
)


class AnalyserController(ADBaseController[AbstractAnalyserDriverIO]):
    def get_deadtime(self, exposure: float | None) -> float:
        return 0


class BaseElectronAnalyserDetector(
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

    If possible, this should be changed to inheirt from a StandardDetector. Currently,
    StandardDetector forces you to use a file writer which doesn't apply here.
    See issue https://github.com/bluesky/ophyd-async/issues/888
    """

    def __init__(
        self,
        name: str,
        driver: TAbstractAnalyserDriverIO,
    ):
        self.controller: AnalyserController = AnalyserController(driver=driver)
        super().__init__(name)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        await self.controller.arm()
        await self.controller.wait_for_idle()

    @AsyncStatus.wrap
    async def stage(self) -> None:
        """Make sure the detector is idle and ready to be used."""
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
        Define property for the driver. Some implementations will store this as a
        reference so it doesn't run into errors with conflicting parents.
        """


class AbstractElectronAnalyserRegionDetector(
    BaseElectronAnalyserDetector[TAbstractAnalyserDriverIO],
    Stageable,
    Generic[TAbstractAnalyserDriverIO, TAbstractBaseRegion],
):
    """
    Extends electron analyser detector to configure specific region settings before data
    acqusition. This object must be passed in a driver and store it as a reference. It
    is designed to only exist inside a plan.
    """

    def __init__(
        self, name: str, driver: TAbstractAnalyserDriverIO, region: TAbstractBaseRegion
    ):
        self._driver_ref = Reference(driver)
        self.region = region
        super().__init__(name, driver)

    @property
    def driver(self) -> TAbstractAnalyserDriverIO:
        # Store as a reference, this implementation will be given a driver so needs to
        # make sure we don't get conflicting parents.
        return self._driver_ref()

    @AsyncStatus.wrap
    async def stage(self) -> None:
        super().stage()
        self.configure_region()

    @abstractmethod
    def configure_region(self):
        """
        Setup analyser with configured region.
        """


TAbstractElectronAnalyserRegionDetector = TypeVar(
    "TAbstractElectronAnalyserRegionDetector",
    bound=AbstractElectronAnalyserRegionDetector,
)


class AbstractElectronAnalyserDetector(
    BaseElectronAnalyserDetector[TAbstractAnalyserDriverIO],
    Generic[TAbstractAnalyserDriverIO, TAbstractBaseSequence, TAbstractBaseRegion],
):
    """
    Electron analyser detector with the additional functionality to load a sequence file
    and create a list of temporary ElectronAnalyserRegionDetector objects. These will
    setup configured region settings before data acquisition.
    """

    def __init__(
        self, prefix: str, name: str, sequence_class: type[TAbstractBaseSequence]
    ):
        self._driver = self._create_driver(prefix)
        self._sequence_class = sequence_class
        super().__init__(name, self.driver)

    @property
    def driver(self) -> TAbstractAnalyserDriverIO:
        # This implementation creates the driver and wants this to be the parent so it
        # can be used with connect() method.
        return self._driver

    def load_sequence(self, filename: str) -> TAbstractBaseSequence:
        return load_json_file_to_class(self._sequence_class, filename)

    @abstractmethod
    def _create_driver(self, prefix: str) -> TAbstractAnalyserDriverIO:
        """
        Define implementation of the driver used for this detector.
        """

    @abstractmethod
    def _create_region_detector(
        self, driver: TAbstractAnalyserDriverIO, region: TAbstractBaseRegion
    ) -> AbstractElectronAnalyserRegionDetector[
        TAbstractAnalyserDriverIO, TAbstractBaseRegion
    ]:
        """
        Define a way to create a temporary detector object that will always setup a
        specific region before acquiring.
        """

    def create_region_detector_list(
        self, filename: str
    ) -> list[
        AbstractElectronAnalyserRegionDetector[
            TAbstractAnalyserDriverIO, TAbstractBaseRegion
        ]
    ]:
        """
        Create a list of detectors that will setup a specific region from the sequence
        file when used.
        """
        seq = self.load_sequence(filename)
        return [
            self._create_region_detector(self.driver, r)
            for r in seq.get_enabled_regions()
        ]


TAbstractElectronAnalyserDetector = TypeVar(
    "TAbstractElectronAnalyserDetector",
    bound=AbstractElectronAnalyserDetector,
)
