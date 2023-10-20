import asyncio
from enum import Enum
from typing import Optional, Sequence

from ophyd_async.core import (
    AsyncStatus,
    DetectorControl,
    DetectorTrigger,
    Device,
)
from ophyd_async.core import SignalR, StandardDetector, DirectoryProvider
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw
from ophyd_async.epics.areadetector.writers import HDFWriter, NDFileHDF
from ophyd_async.epics.areadetector.drivers import ADBaseShapeProvider
from bluesky.protocols import HasHints, Hints


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
    """base rate"""

    maximum_readings_per_frame: int
    """An upper limit on the dimension of frames collected during a collection"""

    minimum_values_per_reading: int
    """A lower bound on the values that will be averaged to create a single reading"""

    idle_acquire: bool
    """Whether the tetramm should be left acquiring after a collection"""

    idle_trigger_state: TetrammTrigger
    """The state the trigger should be left in when no collection is running"""

    idle_averaging_time: float
    """Time that readings should be averaged over then no collection is running"""

    idle_values_per_reading: int
    """The values to be averaged for each sample when no collection is running"""

    collection_resolution: TetrammResolution = TetrammResolution.TwentyFourBits
    """Default resolution to be used for collections"""

    collection_geometry: TetrammGeometry = TetrammGeometry.Square
    """Default geometry to be used for collections"""

    collection_range: TetrammRange = TetrammRange.uA
    """Default range to be used for collections"""

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


class TetrammController(DetectorControl):
    def __init__(
        self,
        drv: TetrammDriver,
        minimum_values_per_reading=5,
        maximum_readings_per_frame=1_000,
        collection_resolution=TetrammResolution.TwentyFourBits,
        collection_geometry=TetrammGeometry.Square,
        collection_range=TetrammRange.uA,
        base_sample_rate=100_000,
        idle_acquire=True,
        idle_trigger_state=TetrammTrigger.FreeRun,
        idle_averaging_time=0.1,
        idle_values_per_reading=10,
    ):
        self._drv = drv

        self.base_sample_rate = base_sample_rate
        self.maximum_readings_per_frame = maximum_readings_per_frame
        self.minimum_values_per_reading = minimum_values_per_reading

        self.idle_acquire = idle_acquire
        self.idle_trigger_state = idle_trigger_state
        self.idle_averaging_time = idle_averaging_time
        self.idle_values_per_reading = idle_values_per_reading

        self.collection_resolution = collection_resolution
        self.collection_geometry = collection_geometry
        self.collection_range = collection_range

    def get_deadtime(self, _exposure: float) -> float:
        return 0.01  # Picked from a hat

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
        if trigger != DetectorTrigger.constant_gate:
            raise ValueError("Only constant gate triggers are supported")

        await self._drv.acquire.set(TetrammAcquire.Stop)
        await self.set_frame_time(exposure)
        await self._drv.trigger_mode.set(TetrammTrigger.ExtTrigger)
        await self._drv.acquire.set(TetrammAcquire.Stop) #remove?
        asyncio.gather(
            self._drv.resolution.set(self.collection_resolution),
            self._drv.range.set(self.collection_range),
            self._drv.geometry.set(self.collection_geometry),
        )
        await self._drv.acquire.set(TetrammAcquire.Acquire)

    async def disarm(self):
        await self._drv.acquire.set(TetrammAcquire.Stop)
        asyncio.gather(
            self._drv.averaging_time.set(self.idle_averaging_time),
            self._drv.values_per_reading.set(self.idle_values_per_reading),
            self._drv.trigger_mode.set(self.idle_trigger_state),
        )

    async def set_frame_time(self, seconds):
        await self._drv.averaging_time.set(seconds / 1_000)
        values_per_reading = (
            seconds * self._drv.base_sample_rate / self._drv.maximum_readings_per_frame
        )
        if values_per_reading < self._drv.minimum_values_per_reading:
            values_per_reading = self._drv.minimum_values_per_reading
        await self._drv.values_per_reading.set(values_per_reading)


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
