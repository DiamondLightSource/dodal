import asyncio
from typing import Annotated as A

from ophyd_async.core import (
    DetectorTriggerLogic,
    PathProvider,
    SignalRW,
    StrictEnum,
)
from ophyd_async.epics.adcore import (
    ADArmLogic,
    ADBaseIO,
    ADImageMode,
    ADWriterType,
    AreaDetector,
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


class Mythen3Driver(ADBaseIO):
    # Non-specific PV's but with mythen3 specific values
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


class Mythen3TriggerLogic(DetectorTriggerLogic):
    """Trigger logic for a Mythen3."""

    def __init__(self, driver: Mythen3Driver):
        self._driver = driver
        # super().__init__(driver=self._driver)

    def get_deadtime(self, config_values) -> float:
        return _DEADTIMES[_BIT_DEPTH]

    # async def prepare(self, trigger_info: TriggerInfo) -> None:
    #     if (exposure := trigger_info.livetime) is not None:
    #         await self._driver.acquire_time.set(exposure)

    #     if trigger_info.trigger is DetectorTrigger.INTERNAL:
    #         await self._driver.trigger_mode.set(Mythen3TriggerMode.INTERNAL)
    #     elif trigger_info.trigger in {
    #         DetectorTrigger.EXTERNAL_LEVEL,
    #         DetectorTrigger.EXTERNAL_EDGE,
    #         DetectorTrigger.EXTERNAL_LEVEL,
    #     }:
    #         await self._driver.trigger_mode.set(Mythen3TriggerMode.EXTERNAL)
    #     else:
    #         raise ValueError(f"Mythen3 does not support {trigger_info.trigger}")

    #     if trigger_info.number_of_exposures == 0:
    #         image_mode = ADImageMode.CONTINUOUS
    #     else:
    #         image_mode = ADImageMode.MULTIPLE
    #     await asyncio.gather(
    #         self._driver.num_images.set(trigger_info.number_of_exposures),
    #         self._driver.image_mode.set(image_mode),
    #     )

    async def prepare_internal(self, num: int, livetime: float, deadtime: float):
        if livetime:
            await self._driver.acquire_time.set(livetime)
        await self._driver.trigger_mode.set(Mythen3TriggerMode.INTERNAL)
        image_mode = ADImageMode.CONTINUOUS if num == 0 else ADImageMode.MULTIPLE
        await asyncio.gather(
            self._driver.num_images.set(num),
            self._driver.image_mode.set(image_mode),
        )

    async def prepare_edge(self, num: int, livetime: float):
        if livetime:
            await self._driver.acquire_time.set(livetime)
        await self._driver.trigger_mode.set(Mythen3TriggerMode.EXTERNAL)
        image_mode = ADImageMode.CONTINUOUS if num == 0 else ADImageMode.MULTIPLE
        await asyncio.gather(
            self._driver.num_images.set(num),
            self._driver.image_mode.set(image_mode),
        )

    async def prepare_level(self, num: int):
        await self.prepare_edge(num, 0.0)


class Mythen3(AreaDetector[Mythen3Driver]):
    """The detector may be configured for an external trigger on a GPIO port,
    which must be done prior to preparing the detector.
    """

    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        drv_suffix: str = DET_SUFFIX,
        writer_type: ADWriterType = ADWriterType.HDF,
        writer_suffix: str | None = "HDF:",
        name: str = "",
    ):
        self.driver = Mythen3Driver(prefix + drv_suffix)

        super().__init__(
            prefix=prefix,
            driver=self.driver,
            arm_logic=ADArmLogic(self.driver),
            trigger_logic=Mythen3TriggerLogic(self.driver),
            path_provider=path_provider,
            writer_type=writer_type,
            writer_suffix=writer_suffix,
            name=name,
        )
