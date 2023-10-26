from enum import Enum
from math import floor
from typing import Generator, Optional

from bluesky.protocols import Hints
from ophyd_async.core import (
    AsyncStatus,
    DetectorControl,
    DetectorTrigger,
    Device,
    DirectoryProvider,
    StandardDetector,
    set_signal_values,
    walk_rw_signals,
)
from ophyd_async.core.device_save_loader import Msg
from ophyd_async.epics.areadetector.drivers import ADBaseShapeProvider
from ophyd_async.epics.areadetector.writers import HDFWriter, NDFileHDF
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw


class TetrammAcquire(Enum):
    Acquire = "Acquire"
    Stop = "Stop"


class TetrammRange(Enum):
    uA = "+- 120 uA"
    nA = "+- 120 nA"


class TetrammTrigger(Enum):
    FreeRun = "Free run"
    ExtTrigger = "Ext. trig."
    ExtBulb = "Ext. bulb"
    ExtGate = "Ext. gate"


class TetrammChannels(Enum):
    One = "1"
    Two = "2"
    Four = "4"


class TetrammResolution(Enum):
    SixteenBits = "16 bits"
    TwentyFourBits = "24 bits"

    def __repr__(self):
        if self == TetrammResolution.SixteenBits:
            return "16bits"
        elif self == TetrammResolution.TwentyFourBits:
            return "24bits"
        else:
            return "Unknown"


class TetrammGeometry(Enum):
    Diamond = "Diamond"
    Square = "Square"


class TetrammDriver(Device):
    base_sample_rate: int
    """base rate - fixed in hardware"""

    maximum_readings_per_frame: int = 1000
    """
    Maximum number of readings per frame

    Actual readings may be lower if higher frame rate is required
    """

    readings_per_frame: int = 1000
    """The number of readings per frame"""

    minimum_values_per_reading: int = 5
    """A lower bound on the values that will be averaged to create a single reading"""

    def __init__(
        self,
        prefix,
        name="",
    ):
        self._prefix = prefix
        self.range = epics_signal_rw(TetrammRange, prefix + "Range")
        self.sample_time = epics_signal_r(float, prefix + "SampleTime_RBV")

        self.values_per_reading = epics_signal_rw(
            int, prefix + "ValuesPerRead_RBV", prefix + "ValuesPerRead"
        )
        self.averaging_time = epics_signal_rw(
            float, prefix + "AveragingTime_RBV", prefix + "AveragingTime"
        )
        self.to_average = epics_signal_r(int, prefix + "NumAverage_RBV")
        self.averaged = epics_signal_r(int, prefix + "NumAveraged_RBV")

        self.acquire = epics_signal_rw(TetrammAcquire, prefix + "Acquire")

        self.overflows = epics_signal_r(int, prefix + "RingOverflows")

        self.channels = epics_signal_rw(TetrammChannels, prefix + "NumChannels")
        self.resolution = epics_signal_rw(TetrammResolution, prefix + "Resolution")
        self.trigger_mode = epics_signal_rw(TetrammTrigger, prefix + "TriggerMode")
        self.bias = epics_signal_rw(bool, prefix + "BiasState")
        self.bias_volts = epics_signal_rw(
            float, prefix + "BiasVoltage", prefix + "BiasVoltage_RBV"
        )
        self.geometry = epics_signal_rw(TetrammGeometry, prefix + "Geometry")

        super().__init__(name=name)

    @property
    def max_frame_rate(self) -> float:
        """Max frame rate in Hz for the current configuration"""
        return 1 / self.minimum_frame_time

    @max_frame_rate.setter
    def max_frame_rate(self, mfr: float):
        self.minimum_frame_time = 1 / mfr

    @property
    def minimum_frame_time(self) -> float:
        sample_time = self.minimum_values_per_reading / self.base_sample_rate
        return self.readings_per_frame * sample_time

    @minimum_frame_time.setter
    def minimum_frame_time(self, frame: float):
        sample_time = self.minimum_values_per_reading / self.base_sample_rate
        self.readings_per_frame = min(
            self.maximum_readings_per_frame, int(floor(frame / sample_time))
        )


class TetrammController(DetectorControl):
    def __init__(
        self,
        drv: TetrammDriver,
        minimum_values_per_reading=5,
        maximum_readings_per_frame=1_000,
        base_sample_rate=100_000,
    ):
        self._drv = drv

        self.base_sample_rate = base_sample_rate
        self.maximum_readings_per_frame = maximum_readings_per_frame
        self.minimum_values_per_reading = minimum_values_per_reading

    def get_deadtime(self, _exposure: float) -> float:
        return 0.001  # Picked from a hat

    @AsyncStatus.wrap
    async def arm(
        self,
        trigger: DetectorTrigger = DetectorTrigger.constant_gate,
        num: int = 0,  # the tetramm has no concept of setting number of exposures
        exposure: Optional[float] = None,
    ):
        if num != 0:
            raise Exception("Tetramm has no concept of setting a number of exposures.")
        if exposure is None:
            raise ValueError("Exposure time is required")
        if trigger != DetectorTrigger.edge_trigger:
            raise ValueError("Only edge triggers are supported")

        await self.set_frame_time(exposure)
        await self._drv.acquire.set(TetrammAcquire.Acquire)

    async def disarm(self):
        await self._drv.acquire.set(TetrammAcquire.Stop)

    async def set_frame_time(self, seconds):
        # It may not always be possible to set the exact collection time if the
        # exposure is not a multiple of the base sample rate. In this case it
        # will always be the closest collection time *below* the requested time
        # to ensure that triggers are not missed.
        values_per_reading = int(
            floor(seconds * self._drv.base_sample_rate / self._drv.readings_per_frame)
        )
        if values_per_reading < self._drv.minimum_values_per_reading:
            raise ValueError(
                f"Exposure ({seconds}) too short to collect required number of readings {self._drv.readings_per_frame}"
            )
        await self._drv.averaging_time.set(seconds / 1_000)
        await self._drv.values_per_reading.set(values_per_reading)


IDLE_TETRAMM = {
    "acquire": TetrammAcquire.Stop,
}

COMMON_TETRAMM = {
    "range": TetrammRange.uA,
    "channels": 4,
    "resolution": TetrammResolution.TwentyFourBits,
    "bias": False,
    "bias_volts": 0,
    "geometry": TetrammGeometry.Square,
}

TRIGGERED_TETRAMM = {
    **COMMON_TETRAMM,
    "trigger_mode": TetrammTrigger.ExtTrigger,
}

FREE_TETRAMM = {
    **COMMON_TETRAMM,
    "sample_time": 0.1,
    "values_per_reading": 10,
    "acquire": TetrammAcquire.Acquire,
    "trigger_mode": TetrammTrigger.FreeRun,
}


def triggered_tetramm(dev: TetrammDriver) -> Generator[Msg, None, None]:
    sigs = walk_rw_signals(dev)
    yield from set_signal_values(
        sigs,
        [
            IDLE_TETRAMM,
            TRIGGERED_TETRAMM,
        ],
    )


def free_tetramm(dev: TetrammDriver) -> Generator[Msg, None, None]:
    sigs = walk_rw_signals(dev)
    yield from set_signal_values(sigs, [IDLE_TETRAMM, FREE_TETRAMM])


class TetrammDetector(StandardDetector):
    def __init__(
        self, prefix: str, directory_provider: DirectoryProvider, name: str = ""
    ) -> None:
        drv = TetrammDriver(prefix + ":DRV:")
        hdf = NDFileHDF(prefix + ":HDF5:")

        self.drv = drv
        self.hdf = hdf

        # TODO: how to make the below, readable signals?
        # self.current_1 = epics_signal_r(float, prefix + ":Cur1:MeanValue_RBV")
        # self.current_2 = epics_signal_r(float, prefix + ":Cur2:MeanValue_RBV")
        # self.current_3 = epics_signal_r(float, prefix + ":Cur3:MeanValue_RBV")
        # self.current_4 = epics_signal_r(float, prefix + ":Cur4:MeanValue_RBV")

        # self.position_x = epics_signal_r(float, prefix + ":PosX:MeanValue_RBV")
        # self.position_y = epics_signal_r(float, prefix + ":PosY:MeanValue_RBV")

        super().__init__(
            TetrammController(drv),
            HDFWriter(
                hdf, directory_provider, lambda: self.name, ADBaseShapeProvider(drv)
            ),
            [drv.values_per_reading, drv.averaging_time, drv.sample_time],
            name,
        )

    @property
    def hints(self) -> Hints:
        return {"fields": [self.name]}
