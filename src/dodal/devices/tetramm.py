import asyncio
from enum import Enum

from ophyd_async.core import (
    AsyncStatus,
    DetectorControl,
    DetectorTrigger,
    Device,
)
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


class Tetramm(Device):
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
        name,
        base_pv,
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
        self._base_pv = base_pv
        self.range = epics_signal_rw(TetrammRange, base_pv + ":DRV:Range")
        self.sample_time = epics_signal_r(float, base_pv + ":DRV:SampleTime_RBV")

        self.values_per_reading = epics_signal_rw(
            int, base_pv + ":DRV:ValuesPerRead_RBV", base_pv + ":DRV:ValuesPerRead"
        )
        self.averaging_time = epics_signal_rw(
            float, base_pv + ":DRV:AveragingTime_RBV", base_pv + ":DRV:AveragingTime"
        )
        self.to_average = epics_signal_r(int, base_pv + ":DRV:NumAverage_RBV")
        self.averaged = epics_signal_r(int, base_pv + ":DRV:NumAveraged_RBV")

        self.acquire = epics_signal_rw(TetrammAcquire, base_pv + ":DRV:Acquire")

        self.overflows = epics_signal_r(int, base_pv + ":DRV:RingOverflows")

        self.channels = epics_signal_rw(TetrammChannels, base_pv + ":DRV:NumChannels")
        self.resolution = epics_signal_rw(
            TetrammResolution, base_pv + ":DRV:Resolution"
        )
        self.trigger_mode = epics_signal_rw(
            TetrammTrigger, base_pv + ":DRV:TriggerMode"
        )
        self.bias = epics_signal_rw(bool, base_pv + ":DRV:BiasState")
        self.bias_volts = epics_signal_rw(
            float, base_pv + ":DRV:BiasVoltage", base_pv + ":DRV:BiasVoltage_RBV"
        )

        self.geometry = epics_signal_rw(TetrammGeometry, base_pv + ":DRV:Geometry")

        self.current_1 = epics_signal_r(float, base_pv + ":Cur1:MeanValue_RBV")
        self.current_2 = epics_signal_r(float, base_pv + ":Cur2:MeanValue_RBV")
        self.current_3 = epics_signal_r(float, base_pv + ":Cur3:MeanValue_RBV")
        self.current_4 = epics_signal_r(float, base_pv + ":Cur4:MeanValue_RBV")

        self.position_x = epics_signal_r(float, base_pv + ":PosX:MeanValue_RBV")
        self.position_y = epics_signal_r(float, base_pv + ":PosY:MeanValue_RBV")

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

        self.set_readable_signals(
            read=[
                self.current_1,
                self.current_2,
                self.current_3,
                self.current_4,
                self.position_x,
                self.position_y,
            ],
            config=[self.values_per_reading, self.averaging_time, self.sample_time],
        )
        super().__init__(name=name)

    async def set_frame_time(self, seconds):
        await self.averaging_time.set(seconds / 1_000)
        values_per_reading = (
            seconds * self.base_sample_rate / self.maximum_readings_per_frame
        )
        if values_per_reading < self.minimum_values_per_reading:
            values_per_reading = self.minimum_values_per_reading
        await self.values_per_reading.set(values_per_reading)

    async def configure_for_collection(self):
        # TODO: Replace with load/save
        # TODO: If load/save isn't happening soon, need to set
        # * channels
        # * bias
        # * trigger? - may be set by TetrammController
        # Collection parameters (values per reading/averaging_time etc) are set via
        # set_frame_time and should be called by the TetrammController when configuring
        # a fly scan.
        await self.acquire.set(TetrammAcquire.Stop)
        asyncio.gather(
            self.resolution.set(self.collection_resolution),
            self.range.set(self.collection_range),
            self.geometry.set(self.collection_geometry),
        )

    async def configure_for_idle(self):
        # TODO: Replace with load/save
        # otherwise need to also set
        # * range
        # * resolution
        # * geometry
        # * channels
        # * bias
        # Maybe should just be set back to how it was before the collection to keep
        # any changes made via the EDM screen
        await self.acquire.set(TetrammAcquire.Stop)
        asyncio.gather(
            self.averaging_time.set(self.idle_averaging_time),
            self.values_per_reading.set(self.idle_values_per_reading),
            self.trigger_mode.set(self.idle_trigger_state),
        )


class TetrammContoller(DetectorControl):
    def __init__(self, drv: Tetramm):
        self._drv = drv

    def get_deadtime(self, _exposure: float) -> float:
        return 0.01  # Picked from a hat

    @AsyncStatus.wrap
    async def arm(
        self,
        trigger: DetectorTrigger = DetectorTrigger.internal,
        _num: int = 0,  # the tetramm has no concept of setting number of exposures
        exposure: Optional[float] = None,
    ):
        if exposure is None:
            raise ValueError("Exposure time is required")
        # TODO: None of the detector trigger variants really fit
        if trigger != DetectorTrigger.constant_gate:
            raise ValueError("Only constant gate triggers are supported")

        await self._drv.acquire.set(TetrammAcquire.Stop)
        await self._drv.set_frame_time(exposure)
        await self._drv.trigger_mode.set(TetrammTrigger.ExtTrigger)
        await self._drv.configure_for_collection()
        await self._drv.acquire.set(TetrammAcquire.Acquire)

    async def disarm(self):
        await self._drv.acquire.set(TetrammAcquire.Stop)
        await self._drv.configure_for_idle()
