import asyncio
from typing import Annotated as A

from ophyd_async.core import (
    DetectorTrigger,
    PathProvider,
    SignalR,
    SignalRW,
    StandardDetector,
    StrictEnum,
    TriggerInfo,
)
from ophyd_async.epics.adcore import (
    ADBaseController,
    ADHDFWriter,
    ADImageMode,
    ADWriter,
    AreaDetector,
    NDArrayBaseIO,
)
from ophyd_async.epics.core import PvSuffix

from dodal.common.beamlines.device_helpers import DET_SUFFIX, HDF5_SUFFIX


class Mythen3TriggerMode(StrictEnum):
    INTERNAL = "Internal"
    EXTERNAL = "External"


class Mythen3ModeSetting(StrictEnum):
    STANDARD = "standard"
    FAST = "fast"
    HIGHGAIN = "highgain"


class Mythen3DetectorState(StrictEnum):
    """Default set of states of an  Mythen3 driver."""

    IDLE = "Idle"
    ERROR = "Error"
    WAITING = "Waiting"
    FINISHED = "Finished"
    TRASMITTING = "Transmitting"
    RUNNING = "Running"
    STOPPED = "Stopped"
    INITIALIZING = "Initializing"
    DISCONNECTED = "Disconnected"
    ABORTED = "Aborted"


class Mythen3BaseIO(NDArrayBaseIO):
    acquire_time: A[SignalRW[float], PvSuffix.rbv("AcquireTime")]
    acquire_period: A[SignalRW[float], PvSuffix.rbv("AcquirePeriod")]
    num_images: A[SignalRW[int], PvSuffix.rbv("NumImages")]
    image_mode: A[SignalRW[ADImageMode], PvSuffix.rbv("ImageMode")]
    detector_state: A[SignalR[Mythen3DetectorState], PvSuffix("DetectorState_RBV")]


class Mythen3Driver(Mythen3BaseIO):
    trigger_mode: A[SignalRW[Mythen3TriggerMode], PvSuffix.rbv("TriggerMode")]
    mode_setting: A[SignalRW[Mythen3ModeSetting], PvSuffix.rbv("Setting")]


class Mythen3Controller(ADBaseController):
    """ADBaseController` for an `Mythen3"""

    def get_deadtime(self, exposure: float | None) -> float:
        return 5e-6

    async def prepare(self, trigger_info: TriggerInfo) -> None:
        if (exposure := trigger_info.livetime) is not None:
            await self.driver.acquire_time.set(exposure)

        if trigger_info.trigger is DetectorTrigger.INTERNAL:
            await self.driver.trigger_mode.set(Mythen3TriggerMode.INTERNAL)
        elif trigger_info.trigger in {
            DetectorTrigger.CONSTANT_GATE,
            DetectorTrigger.EDGE_TRIGGER,
        }:
            await self.driver.trigger_mode.set(Mythen3TriggerMode.EXTERNAL)
        else:
            raise ValueError(f"Mythen3 does not support {trigger_info.trigger}")

        if trigger_info.total_number_of_exposures == 0:
            image_mode = ADImageMode.CONTINUOUS
        else:
            image_mode = ADImageMode.MULTIPLE
        await asyncio.gather(
            self.driver.num_images.set(trigger_info.total_number_of_exposures),
            self.driver.image_mode.set(image_mode),
        )


class Mythen3(AreaDetector):
    """
    The detector may be configured for an external trigger on a GPIO port,
    which must be done prior to preparing the detector
    """

    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        drv_suffix=DET_SUFFIX,
        writer_cls: type[ADWriter] = ADHDFWriter,
        fileio_suffix: str | None = HDF5_SUFFIX,
        name: str = "",
    ):
        driver = Mythen3Driver(prefix + drv_suffix)
        controller = Mythen3Controller(driver)

        writer = writer_cls.with_io(
            prefix,
            path_provider,
            dataset_source=driver,
            fileio_suffix=fileio_suffix,
        )

        super().__init__(
            controller=controller,
            writer=writer,
            # plugins=plugins,
            name=name,
            # config_sigs=config_sigs,
        )


class MAC(StandardDetector):
    def __init__(self, name=""):
        pass
