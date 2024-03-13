import asyncio
from enum import Enum
from math import floor
from typing import Generator, Optional, Sequence

import bluesky.plan_stubs as bps
from bluesky.protocols import Hints
from ophyd_async.core import (
    AsyncStatus,
    DetectorControl,
    DetectorTrigger,
    Device,
    DirectoryProvider,
    ShapeProvider,
    StandardDetector,
    set_and_wait_for_value,
    set_signal_values,
    walk_rw_signals,
)
from ophyd_async.core.device_save_loader import Msg
from ophyd_async.epics.areadetector.utils import ad_r, ad_rw, stop_busy_record
from ophyd_async.epics.areadetector.writers import HDFWriter, NDFileHDF
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw


class TetrammRange(str, Enum):
    uA = "+- 120 uA"
    nA = "+- 120 nA"


class TetrammTrigger(str, Enum):
    FreeRun = "Free run"
    ExtTrigger = "Ext. trig."
    ExtBulb = "Ext. bulb"
    ExtGate = "Ext. gate"


class TetrammChannels(str, Enum):
    One = "1"
    Two = "2"
    Four = "4"


class TetrammResolution(str, Enum):
    SixteenBits = "16 bits"
    TwentyFourBits = "24 bits"

    def __repr__(self):
        if self == TetrammResolution.SixteenBits:
            return "16bits"
        elif self == TetrammResolution.TwentyFourBits:
            return "24bits"
        else:
            return "Unknown"


class TetrammGeometry(str, Enum):
    Diamond = "Diamond"
    Square = "Square"


class TetrammDriver(Device):
    def __init__(
        self,
        prefix: str,
        name: str = "",
    ):
        self._prefix = prefix
        self.range = ad_rw(TetrammRange, prefix + "Range")
        self.sample_time = ad_r(float, prefix + "SampleTime")

        self.values_per_reading = ad_rw(int, prefix + "ValuesPerRead")
        self.averaging_time = ad_rw(float, prefix + "AveragingTime")
        self.to_average = ad_r(int, prefix + "NumAverage")
        self.averaged = ad_r(int, prefix + "NumAveraged")

        self.acquire = ad_rw(bool, prefix + "Acquire")

        # this PV is special, for some reason it doesn't have a _RBV suffix...
        self.overflows = epics_signal_r(int, prefix + "RingOverflows")

        self.num_channels = ad_rw(TetrammChannels, prefix + "NumChannels")
        self.resolution = ad_rw(TetrammResolution, prefix + "Resolution")
        self.trigger_mode = ad_rw(TetrammTrigger, prefix + "TriggerMode")
        self.bias = ad_rw(bool, prefix + "BiasState")
        self.bias_volts = ad_rw(float, prefix + "BiasVoltage")
        self.geometry = ad_rw(TetrammGeometry, prefix + "Geometry")
        self.nd_attributes_file = epics_signal_rw(str, prefix + "NDAttributesFile")

        super().__init__(name=name)


class TetrammController(DetectorControl):
    def __init__(
        self,
        drv: TetrammDriver,
        minimum_values_per_reading=5,
        maximum_readings_per_frame=1_000,
        base_sample_rate=100_000,
        readings_per_frame=1_000,
    ):
        self._drv = drv

        self.base_sample_rate = base_sample_rate
        """base rate - fixed in hardware"""

        self.maximum_readings_per_frame = maximum_readings_per_frame
        """
        Maximum number of readings per frame
        Actual readings may be lower if higher frame rate is required
        """

        self.minimum_values_per_reading = minimum_values_per_reading
        """A lower bound on the values that will be averaged to create a single reading"""

        self.readings_per_frame = readings_per_frame
        """The number of readings per frame"""

    def get_deadtime(self, _exposure: float) -> float:
        return 0.001  # Picked from a hat

    async def arm(
        self,
        trigger: DetectorTrigger = DetectorTrigger.internal,
        num: int = 0,
        exposure: Optional[float] = None,
    ) -> AsyncStatus:
        """Arms the tetramm.

        Note that num is meaningless in this context, and is ignored.
        """
        if exposure is None:
            raise ValueError("Exposure time is required")
        if trigger not in {DetectorTrigger.edge_trigger, DetectorTrigger.constant_gate}:
            raise ValueError("Only edge triggers are supported")

        # trigger mode must be set first and on it's own!
        await self._drv.trigger_mode.set(TetrammTrigger.ExtTrigger)

        await asyncio.gather(
            self._drv.averaging_time.set(exposure), self.set_frame_time(exposure)
        )

        status = await set_and_wait_for_value(self._drv.acquire, 1)

        return status

    async def disarm(self):
        await stop_busy_record(self._drv.acquire, 0, timeout=1)

    async def set_frame_time(self, seconds):
        # It may not always be possible to set the exact collection time if the
        # exposure is not a multiple of the base sample rate. In this case it
        # will always be the closest collection time *below* the requested time
        # to ensure that triggers are not missed.
        values_per_reading = int(
            floor(seconds * self.base_sample_rate / self.readings_per_frame)
        )
        if values_per_reading < self.minimum_values_per_reading:
            raise ValueError(
                f"Exposure ({seconds}) too short to collect required number of readings {self.readings_per_frame}. Values per reading is {values_per_reading}, seconds is : {seconds}"
            )
        await self._drv.values_per_reading.set(values_per_reading)

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


# TODO: need to change this name.
MAX_CHANNELS = 11

IDLE_TETRAMM = {
    "drv.acquire": 0,
}

COMMON_TETRAMM = {
    "drv.range": TetrammRange.uA,
    "drv.num_channels": "4",
    "drv.resolution": TetrammResolution.TwentyFourBits,
    "drv.geometry": TetrammGeometry.Square,
}

TRIGGERED_TETRAMM = {
    **COMMON_TETRAMM,
    "drv.trigger_mode": TetrammTrigger.ExtTrigger,
}

FREE_TETRAMM = {
    **COMMON_TETRAMM,
    "drv.values_per_reading": 10,
    "drv.averaging_time": 0.1,
    "drv.trigger_mode": TetrammTrigger.FreeRun,
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
    """Freerun the tetramm, setting it to acquire so diodes update."""
    sigs = walk_rw_signals(dev)
    yield from set_signal_values(sigs, [IDLE_TETRAMM, FREE_TETRAMM])
    yield from bps.abs_set(dev.drv.acquire, 1)


class TetrammShapeProvider(ShapeProvider):
    def __init__(self, controller: TetrammController) -> None:
        self.controller = controller

    async def __call__(self) -> Sequence[int]:
        return [MAX_CHANNELS, self.controller.readings_per_frame]


class TetrammDetector(StandardDetector):
    def __init__(
        self,
        prefix: str,
        directory_provider: DirectoryProvider,
        name: str,
        **scalar_sigs: str,
    ) -> None:
        drv = TetrammDriver(prefix + "DRV:")
        hdf = NDFileHDF(prefix + "HDF5:")

        self.drv = drv
        self.hdf = hdf

        # TODO: how to make the below, readable signals?
        # self.current_1 = ad_r(float, prefix + ":Cur1:MeanValue")
        # self.current_2 = ad_r(float, prefix + ":Cur2:MeanValue")
        # self.current_3 = ad_r(float, prefix + ":Cur3:MeanValue")
        # self.current_4 = ad_r(float, prefix + ":Cur4:MeanValue")

        # self.position_x = ad_r(float, prefix + ":PosX:MeanValue")
        # self.position_y = ad_r(float, prefix + ":PosY:MeanValue")
        controller = TetrammController(drv)
        super().__init__(
            controller,
            HDFWriter(
                hdf,
                directory_provider,
                lambda: self.name,
                TetrammShapeProvider(controller),
                **scalar_sigs,
            ),
            [drv.values_per_reading, drv.averaging_time, drv.sample_time],
            name,
        )

    @property
    def hints(self) -> Hints:
        return {"fields": [self.name]}
