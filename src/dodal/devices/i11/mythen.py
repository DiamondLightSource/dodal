import asyncio
from typing import Annotated as A

from ophyd_async.core import (
    DetectorTrigger,
    PathProvider,
    SignalRW,
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

from dodal.common.beamlines.device_helpers import DET_SUFFIX


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


class Mythen3Driver(NDArrayBaseIO):
    acquire_time: A[SignalRW[float], PvSuffix.rbv("AcquireTime")]
    acquire_period: A[SignalRW[float], PvSuffix.rbv("AcquirePeriod")]
    num_images: A[SignalRW[int], PvSuffix.rbv("NumImages")]
    image_mode: A[SignalRW[ADImageMode], PvSuffix.rbv("ImageMode")]

    # Non-specific PV's but with mythen3 specific values
    detector_state: A[SignalRW[Mythen3DetectorState], PvSuffix("DetectorState_RBV")]
    trigger_mode: A[SignalRW[Mythen3TriggerMode], PvSuffix.rbv("TriggerMode")]

    # mythen3 specific PV's
    mode_setting: A[SignalRW[Mythen3ModeSetting], PvSuffix.rbv("Setting")]
    bit_depth: A[SignalRW[int], PvSuffix.rbv("BitDepth")]
    beam_energy: A[SignalRW[int], PvSuffix.rbv("BeamEnergy")]
    threshold: A[SignalRW[int], PvSuffix.rbv("Counter1Threshold")]
    threshold2: A[SignalRW[int], PvSuffix.rbv("Counter2Threshold")]
    threshold3: A[SignalRW[int], PvSuffix.rbv("Counter3Threshold")]
    global_threshold: A[SignalRW[int], PvSuffix.rbv("ThresholdEnergy")]


"""
Re. _DEADTIMES

see: https://doi.org/10.1107/S1600577525000438
Journal of Synchrotron Radiation, Volume 32, Part 2, March 2025, Pages 365-377
See Section 3.3, Table 2, Section 3.4 and Table 3

Note: Maximum frame rate of MYTHEN III is a function of the number of counters and of
the bit depth.

These numbers neglect possible limitations arising from the DAQ computing and network
system. Expect ~1 order of magnitude less

Our mythen3 is currently set up to use 3 counters, and 32bit depth. The deadtimes are
for 3 counters only. We can run faster with less counters/bit depth

The maximum frame rate of the detector scales both with the number of counters being
read out and with the bit depth, which can be configured to 24 (streamed out as 32 bit),
16 or 8 bits see Table 3.

"""
_DEADTIMES = {
    32: 1 / (30 * 1000),  # values reported in frame rate (kHz)
    24: 1 / (40 * 1000),
    16: 1 / (60 * 1000),
    8: 1 / (120 * 1000),
}

_BIT_DEPTH = 24


class Mythen3Controller(ADBaseController):
    """ADBaseController` for a Mythen3"""

    def __init__(self, driver: Mythen3Driver):
        self._driver = driver
        super().__init__(driver=self._driver)

    def get_deadtime(self, exposure: float | None) -> float:
        return _DEADTIMES[_BIT_DEPTH]

    async def prepare(self, trigger_info: TriggerInfo) -> None:
        if (exposure := trigger_info.livetime) is not None:
            await self._driver.acquire_time.set(exposure)

        if trigger_info.trigger is DetectorTrigger.INTERNAL:
            await self._driver.trigger_mode.set(Mythen3TriggerMode.INTERNAL)
        elif trigger_info.trigger in {
            DetectorTrigger.CONSTANT_GATE,
            DetectorTrigger.EDGE_TRIGGER,
            DetectorTrigger.VARIABLE_GATE,
        }:
            await self._driver.trigger_mode.set(Mythen3TriggerMode.EXTERNAL)
        else:
            raise ValueError(f"Mythen3 does not support {trigger_info.trigger}")

        if trigger_info.total_number_of_exposures == 0:
            image_mode = ADImageMode.CONTINUOUS
        else:
            image_mode = ADImageMode.MULTIPLE
        await asyncio.gather(
            self._driver.num_images.set(trigger_info.total_number_of_exposures),
            self._driver.image_mode.set(image_mode),
        )


class Mythen3(AreaDetector[Mythen3Controller]):
    """
    The detector may be configured for an external trigger on a GPIO port,
    which must be done prior to preparing the detector
    """

    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        drv_suffix: str = DET_SUFFIX,
        writer_cls: type[ADWriter] = ADHDFWriter,
        fileio_suffix: str | None = "HDF:",
        name: str = "",
    ):
        self.driver = Mythen3Driver(prefix + drv_suffix)
        self.controller = Mythen3Controller(driver=self.driver)

        self.writer = writer_cls.with_io(
            prefix,
            path_provider,
            dataset_source=self.driver,
            fileio_suffix=fileio_suffix,
        )

        super().__init__(
            controller=self.controller,
            writer=self.writer,
            name=name,
        )  # plugins=plugins # config_sigs=config_sigs
