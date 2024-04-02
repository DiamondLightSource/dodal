import asyncio
from enum import Enum
from typing import Dict, Optional

from bluesky.protocols import HasHints, Hints
from ophyd_async.core import (
    AsyncStatus,
    DetectorControl,
    DetectorTrigger,
    DirectoryProvider,
    StandardDetector,
    set_and_wait_for_value,
)
from ophyd_async.epics.areadetector.drivers import ADBase, ADBaseShapeProvider
from ophyd_async.epics.areadetector.utils import ImageMode, ad_rw, stop_busy_record
from ophyd_async.epics.areadetector.writers import HDFWriter, NDFileHDF, NDPluginStats


class AdSimTriggerMode(str, Enum):
    Internal = "Internal"
    External = "External"


class AdSimDriver(ADBase):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.image_mode = ad_rw(ImageMode, prefix + "ImageMode")
        self.trigger_mode = ad_rw(AdSimTriggerMode, prefix + "TriggerMode")
        # Acquisition period, including deadtime
        self.acquire_period = ad_rw(float, prefix + "AcquirePeriod")
        # Exposures per image
        self.num_exposures = ad_rw(int, prefix + "NumExposures")
        super().__init__(prefix, name=name)


class AdSimController(DetectorControl):
    TRIGGER_SOURCE: Dict[DetectorTrigger, AdSimTriggerMode] = {
        DetectorTrigger.internal: AdSimTriggerMode.Internal,
        DetectorTrigger.constant_gate: AdSimTriggerMode.External,
        DetectorTrigger.edge_trigger: AdSimTriggerMode.External,
        DetectorTrigger.variable_gate: AdSimTriggerMode.External,
    }

    def __init__(self, driver: AdSimDriver) -> None:
        self.driver = driver

    async def arm(
        self,
        trigger: DetectorTrigger = DetectorTrigger.internal,
        num: int = 0,
        exposure: Optional[float] = None,
    ) -> AsyncStatus:
        if num == 0:
            image_mode = ImageMode.continuous
        elif num == 1:
            image_mode = ImageMode.single
        else:
            image_mode = ImageMode.multiple

        if exposure is not None:
            await self.driver.acquire_time.set(exposure)

        await asyncio.gather(
            self.driver.trigger_mode.set(self.TRIGGER_SOURCE[trigger]),
            self.driver.num_images.set(num),
            self.driver.image_mode.set(image_mode),
        )

        return await set_and_wait_for_value(self.driver.acquire, True)

    async def disarm(self):
        await stop_busy_record(self.driver.acquire, False, timeout=1)

    def get_deadtime(self, exposure: float) -> float:
        return asyncio.run(self.driver.acquire_period.get_value()) - exposure


class AdSimDetector(StandardDetector, HasHints):
    """
    Ophyd-async implementation of the SimAreaDetector
    """

    def __init__(
        self,
        name: str,
        prefix: str,
        directory_provider: DirectoryProvider,
    ):
        drv = AdSimDriver(prefix + "CAM:")
        hdf = NDFileHDF(prefix + "HDF5:")

        self.drv = drv
        self.hdf = hdf
        self.stats = NDPluginStats(prefix + "STAT:")

        super().__init__(
            AdSimController(drv),
            HDFWriter(
                hdf,
                directory_provider,
                lambda: self.name,
                ADBaseShapeProvider(drv),
                sum="StatsTotal",
            ),
            config_sigs=[drv.acquire_time, drv.acquire],
            name=name,
        )

    @property
    def hints(self) -> Hints:
        return self.writer.hints
