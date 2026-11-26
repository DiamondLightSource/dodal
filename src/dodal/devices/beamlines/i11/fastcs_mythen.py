from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated as A

import numpy as np
from ophyd_async.core import (
    AsyncStatus,
    DetectorAcquireLogic,
    DetectorDataLogic,
    DetectorTriggerLogic,
    PathProvider,
    SignalR,
    SignalRW,
    SignalW,
    StandardDetector,
    StreamableDataProvider,
    StreamResourceDataProvider,
    StreamResourceInfo,
    StrictEnum,
    set_and_wait_for_other_value,
    wait_for_value,
)
from ophyd_async.epics.core import EpicsDevice, PvSuffix


class Mythen3TriggerMode(StrictEnum):
    AUTO = "Auto"
    TRIGGER = "Trigger"
    GATING = "Gating"
    TRIGGER_GATING = "Trigger_Gating"


class Mythen3DetectorState(StrictEnum):
    """Default set of states of an  Mythen3 driver."""

    IDLE = "Idle"
    ERROR = "Error"
    WAITING = "Waiting"
    RUN_FINISHED = "RunFinished"
    TRANSMITTING = "Transmitting"
    RUNNING = "Running"
    STOPPED = "Stopped"


class FastCSMythen3Driver(EpicsDevice):
    trigger_mode: A[SignalW[Mythen3TriggerMode], PvSuffix("TriggerMode")]
    detector_status: A[SignalR[Mythen3DetectorState], PvSuffix("DetectorStatus")]

    frames: A[SignalRW[int], PvSuffix.rbv("FramesPerAcq")]
    triggers: A[SignalRW[int], PvSuffix.rbv("NumOfTriggers")]

    exposure_time: A[SignalRW[float], PvSuffix.rbv("ExposureTime")]
    period: A[SignalRW[float], PvSuffix.rbv("PeriodBetweenFrames")]

    file_name: A[SignalRW[str], PvSuffix.rbv("FileName")]
    file_path: A[SignalRW[str], PvSuffix.rbv("FilePath")]

    acquire: A[SignalRW[bool], PvSuffix("AcquisitionStart")]
    stop_acquire: A[SignalRW[bool], PvSuffix("AcquisitionStop")]

    frames_written: A[SignalR[int], PvSuffix("FramesWritten")]
    hostname: A[SignalR[str], PvSuffix("Hostname")]

    bitdepth: A[SignalRW[int], PvSuffix("Bitdepth")]


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


class FastCSMythen3TriggerLogic(DetectorTriggerLogic):
    """Trigger logic for a FastCS Mythen3."""

    def __init__(self, driver: FastCSMythen3Driver):
        self._driver = driver

    def get_deadtime(self, config_values) -> float:
        return _DEADTIMES[_BIT_DEPTH]

    async def prepare_internal(self, num: int, livetime: float, deadtime: float):
        # This is actually running in the external start mode as in
        # https://github.com/bluesky/ophyd-async/issues/1527. Once this is it's own mode
        # we can use that instead.
        if livetime:
            await self._driver.exposure_time.set(livetime)
        await self._driver.trigger_mode.set(Mythen3TriggerMode.TRIGGER)
        await self._driver.frames.set(num)
        await self._driver.triggers.set(1)

    async def prepare_edge(self, num: int, livetime: float):
        if livetime:
            await self._driver.exposure_time.set(livetime)
        await self._driver.trigger_mode.set(Mythen3TriggerMode.TRIGGER)
        await self._driver.frames.set(1)
        await self._driver.triggers.set(num)

    async def prepare_level(self, num: int):
        await self._driver.trigger_mode.set(Mythen3TriggerMode.TRIGGER_GATING)
        await self._driver.frames.set(num)


class FastCSMythen3ArmLogic(DetectorAcquireLogic):
    def __init__(self, driver: FastCSMythen3Driver):
        self.driver = driver
        self.acquire_status: AsyncStatus | None = None

    async def start_acquiring(self):
        await set_and_wait_for_other_value(
            self.driver.acquire, True, self.driver.frames_written, 0
        )

    async def wait_for_idle(self):
        await wait_for_value(
            self.driver.detector_status, Mythen3DetectorState.IDLE, timeout=None
        )

    async def ensure_stopped(self):
        await self.driver.stop_acquire.set(True)


@dataclass
class FastCSMythen3DataLogic(DetectorDataLogic):
    path_provider: PathProvider
    driver: FastCSMythen3Driver
    datakey_suffix: str = ""
    hinted: bool = True

    async def prepare_unbounded(self, datakey_name: str) -> StreamableDataProvider:
        # Work out where to write
        path_info = self.path_provider(datakey_name)

        directory_path = f"{path_info.directory_path}/"

        await self.driver.file_path.set(directory_path)
        await self.driver.file_name.set(path_info.filename)

        main_dataset = StreamResourceInfo(
            data_key=datakey_name,
            shape=(1, 32000),
            chunk_shape=(1, 1, 32000),
            dtype_numpy=np.dtype(np.uint8).str,
            parameters={"dataset": "/data"},
        )
        return StreamResourceDataProvider(
            uri=f"{path_info.directory_uri}{path_info.filename}_virtual_0.h5",
            resources=[main_dataset],
            mimetype="application/x-hdf5",
            collections_written_signal=self.driver.frames_written,
            flush_signal=None,
        )

    def get_hinted_fields(self, datakey_name: str) -> Sequence[str]:
        return [datakey_name] if self.hinted else []


class FastCSMythen3(StandardDetector):
    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        name: str = "",
    ):
        self.driver = FastCSMythen3Driver(prefix)

        super().__init__(name=name)

        self.add_detector_logics(
            FastCSMythen3DataLogic(
                driver=self.driver,
                path_provider=path_provider,
            ),
            self.get_detector_trigger_logic(),
            FastCSMythen3ArmLogic(self.driver),
        )

        # configuration signals
        self.add_config_signals(self.driver.hostname)

    def get_detector_trigger_logic(self) -> DetectorTriggerLogic:
        return FastCSMythen3TriggerLogic(self.driver)
