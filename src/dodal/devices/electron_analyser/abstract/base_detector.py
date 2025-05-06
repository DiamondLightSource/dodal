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
    DEFAULT_TIMEOUT,
    AsyncStatus,
    Device,
    Reference,
    set_and_wait_for_value,
)
from ophyd_async.core._protocol import AsyncConfigurable, AsyncReadable
from ophyd_async.epics.adcore import (
    DEFAULT_GOOD_STATES,
    ADState,
    stop_busy_record,
)

from dodal.devices.electron_analyser.abstract.base_analyser_io import (
    AbstractAnalyserDriverIO,
    TAbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.abstract.base_region import (
    TAbstractBaseRegion,
    TAbstractBaseSequence,
)


class AnalyserController:
    def __init__(
        self,
        driver: AbstractAnalyserDriverIO,
        good_states: frozenset[ADState] = DEFAULT_GOOD_STATES,
    ) -> None:
        self.driver = driver
        self.good_states = good_states
        self.frame_timeout = DEFAULT_TIMEOUT
        self._arm_status: AsyncStatus | None = None

    async def arm(self):
        self._arm_status = await self.start_acquiring_driver_and_ensure_status()

    async def disarm(self):
        # We can't use caput callback as we already used it in arm() and we can't have
        # 2 or they will deadlock
        await stop_busy_record(self.driver.acquire, False, timeout=1)

    async def start_acquiring_driver_and_ensure_status(self) -> AsyncStatus:
        """Start acquiring driver, raising ValueError if the detector is in a bad state.
        This sets driver.acquire to True, and waits for it to be True up to a timeout.
        Then, it checks that the DetectorState PV is in DEFAULT_GOOD_STATES,
        and otherwise raises a ValueError.
        :returns AsyncStatus:
            An AsyncStatus that can be awaited to set driver.acquire to True and perform
            subsequent raising (if applicable) due to detector state.
        """
        status = await set_and_wait_for_value(
            self.driver.acquire,
            True,
            timeout=DEFAULT_TIMEOUT,
            wait_for_set_completion=False,
        )

        async def complete_acquisition() -> None:
            # NOTE: possible race condition here between the callback from
            # set_and_wait_for_value and the detector state updating.
            await status
            state = await self.driver.detector_state.get_value()
            if state not in self.good_states:
                raise ValueError(
                    f"Final detector state {state.value} not "
                    "in valid end states: {self.good_states}"
                )

        return AsyncStatus(complete_acquisition())

    async def wait_for_idle(self):
        if self._arm_status and not self._arm_status.done:
            await self._arm_status
        self._arm_status = None


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
    """

    def __init__(
        self,
        name: str,
        driver: TAbstractAnalyserDriverIO,
    ):
        self.driver_ref: Reference[TAbstractAnalyserDriverIO] = Reference(driver)
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
        return await self.driver_ref().read()

    async def describe(self) -> dict[str, DataKey]:
        data = await self.driver_ref().describe()
        # Correct the shape for image
        prefix = self.driver_ref().name + "-"
        energy_size = len(await self.driver_ref().energy_axis.get_value())
        angle_size = len(await self.driver_ref().angle_axis.get_value())
        data[prefix + "image"]["shape"] = [angle_size, energy_size]
        return data

    async def read_configuration(self) -> dict[str, Reading]:
        return await self.driver_ref().read_configuration()

    async def describe_configuration(self) -> dict[str, DataKey]:
        return await self.driver_ref().describe_configuration()


class AbstractElectronAnalyserRegionDetector(
    BaseElectronAnalyserDetector[TAbstractAnalyserDriverIO],
    Stageable,
    Generic[TAbstractAnalyserDriverIO, TAbstractBaseRegion],
):
    """
    Extends electron analyser detector to configure specific region settings before data
    acqusition.
    """

    def __init__(
        self, name: str, driver: TAbstractAnalyserDriverIO, region: TAbstractBaseRegion
    ):
        super().__init__(name, driver)
        self.region = region

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
    and create a list of ElectronAnalyserRegionDetector objects. These will setup
    configured region settings before data acquisition.
    """

    @abstractmethod
    def load_sequence(self, filename: str) -> TAbstractBaseSequence:
        """
        Method to read in sequence file into a sequence class.
        """

    @abstractmethod
    def _create_region_detector(
        self, driver: TAbstractAnalyserDriverIO, region: TAbstractBaseRegion
    ) -> AbstractElectronAnalyserRegionDetector[
        TAbstractAnalyserDriverIO, TAbstractBaseRegion
    ]:
        """
        Define a way to create a detector that will configure to a specific region.
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
            self._create_region_detector(self.driver_ref(), r)
            for r in seq.get_enabled_regions()
        ]


TAbstractElectronAnalyserDetector = TypeVar(
    "TAbstractElectronAnalyserDetector",
    bound=AbstractElectronAnalyserDetector,
)
