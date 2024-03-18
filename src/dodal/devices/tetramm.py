import asyncio
from enum import Enum
from typing import Generator, Sequence

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
        # self.sample_time = ad_r(float, prefix + "SampleTime")

        self.values_per_reading = ad_rw(int, prefix + "ValuesPerRead")
        self.averaging_time = ad_rw(float, prefix + "AveragingTime")
        # self.to_average = ad_r(int, prefix + "NumAverage")
        # self.averaged = ad_r(int, prefix + "NumAveraged")

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
    """Controller for a TetrAMM current monitor

    Attributes:
        base_sample_rate (int): Fixed in hardware

    Args:
        drv (TetrammDriver): A configured driver for the device
        maximum_readings_per_frame (int): Maximum number of readings per frame: actual readings may be lower if higher frame rate is required
        minimum_values_per_reading (int): Lower bound on the values that will be averaged to create a single reading
        readings_per_frame (int): Actual number of readings per frame.

    """

    base_sample_rate: int = 100_000

    def __init__(
        self,
        drv: TetrammDriver,
        minimum_values_per_reading: int = 5,
        maximum_readings_per_frame: int = 1_000,
        readings_per_frame: int = 1_000,
    ):
        # TODO: Are any of these also fixed by hardware constraints?
        self._drv = drv
        self.maximum_readings_per_frame = maximum_readings_per_frame
        self.minimum_values_per_reading = minimum_values_per_reading
        self.readings_per_frame = readings_per_frame

    def get_deadtime(self, exposure: float) -> float:
        # 2 internal clock cycles. Best effort approximation
        return 2 / self.base_sample_rate

    async def arm(
        self,
        trigger: DetectorTrigger,
        num: int,
        exposure: float,
    ) -> AsyncStatus:
        """Arms the TetrAMM

        Args:
            trigger (DetectorTrigger): Trigger type: supports edge_trigger, constant_gate
            num (int): ignored
            exposure (float): Exposure time in seconds

        Raises:
            ValueError: If DetectorTrigger is not supported
        """
        if trigger not in {DetectorTrigger.edge_trigger, DetectorTrigger.constant_gate}:
            raise ValueError("Only edge triggers are supported")

        # trigger mode must be set first and on its own!
        await self._drv.trigger_mode.set(TetrammTrigger.ExtTrigger)

        await asyncio.gather(
            self._drv.averaging_time.set(exposure), self.set_frame_time(exposure)
        )

        status = await set_and_wait_for_value(self._drv.acquire, 1)

        return status

    async def disarm(self):
        await stop_busy_record(self._drv.acquire, 0, timeout=1)

    async def set_frame_time(self, frame_time: float):
        """Tries to set the exposure time of a single frame.

        As during the  exposure time, the device must collect an integer number
        of readings, in the case where the frame_time is not a multiple of the base
        sample rate, it will be lowered to the prior multiple ot ensure triggers
        are not missed.

        Args:
            frame_time (float): The time for a single frame in seconds

        Raises:
            ValueError: If frame_time is too low to collect the required number
            of readings per frame.
        """

        values_per_reading: int = int(
            frame_time * self.base_sample_rate / self.readings_per_frame
        )

        if values_per_reading < self.minimum_values_per_reading:
            raise ValueError(
                f"frame_time {frame_time} is too low to collect at least \
                {self.minimum_values_per_reading} values per reading, at \
                {self.readings_per_frame} readings per frame."
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
        time_per_reading = self.minimum_values_per_reading / self.base_sample_rate
        return self.readings_per_frame * time_per_reading

    @minimum_frame_time.setter
    def minimum_frame_time(self, frame: float):
        time_per_reading = self.minimum_values_per_reading / self.base_sample_rate
        self.readings_per_frame = int(
            min(self.maximum_readings_per_frame, frame / time_per_reading)
        )


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
    max_channels = 11

    def __init__(self, controller: TetrammController) -> None:
        self.controller = controller

    async def __call__(self) -> Sequence[int]:
        return [self.max_channels, self.controller.readings_per_frame]


# TODO: Support MeanValue signals https://github.com/DiamondLightSource/dodal/issues/337
class TetrammDetector(StandardDetector):
    def __init__(
        self,
        prefix: str,
        directory_provider: DirectoryProvider,
        name: str,
        **scalar_sigs: str,
    ) -> None:
        self.drv = TetrammDriver(prefix + "DRV:")
        self.hdf = NDFileHDF(prefix + "HDF5:")
        controller = TetrammController(self.drv)
        super().__init__(
            controller,
            HDFWriter(
                self.hdf,
                directory_provider,
                lambda: self.name,
                TetrammShapeProvider(controller),
                **scalar_sigs,
            ),
            [
                self.drv.values_per_reading,
                self.drv.averaging_time,
                # self.drv.sample_time,
            ],
            name,
        )

    @property
    def hints(self) -> Hints:
        return {"fields": [self.name]}
