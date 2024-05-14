import asyncio
from enum import Enum
from typing import Sequence

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
)
from ophyd_async.epics.areadetector.utils import stop_busy_record
from ophyd_async.epics.areadetector.writers import HDFWriter, NDFileHDF
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw
from ophyd_async.epics.signal.signal import epics_signal_rw_rbv


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
        self.range = epics_signal_rw_rbv(TetrammRange, prefix + "Range")
        self.sample_time = epics_signal_r(float, prefix + "SampleTime_RBV")

        self.values_per_reading = epics_signal_rw_rbv(int, prefix + "ValuesPerRead")
        self.averaging_time = epics_signal_rw_rbv(float, prefix + "AveragingTime")
        self.to_average = epics_signal_r(int, prefix + "NumAverage_RBV")
        self.averaged = epics_signal_r(int, prefix + "NumAveraged_RBV")

        self.acquire = epics_signal_rw_rbv(bool, prefix + "Acquire")

        # this PV is special, for some reason it doesn't have a _RBV suffix...
        self.overflows = epics_signal_r(int, prefix + "RingOverflows")

        self.num_channels = epics_signal_rw_rbv(TetrammChannels, prefix + "NumChannels")
        self.resolution = epics_signal_rw_rbv(TetrammResolution, prefix + "Resolution")
        self.trigger_mode = epics_signal_rw_rbv(TetrammTrigger, prefix + "TriggerMode")
        self.bias = epics_signal_rw_rbv(bool, prefix + "BiasState")
        self.bias_volts = epics_signal_rw_rbv(float, prefix + "BiasVoltage")
        self.geometry = epics_signal_rw_rbv(TetrammGeometry, prefix + "Geometry")
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
        num: int,
        trigger: DetectorTrigger,
        exposure: float,
    ) -> AsyncStatus:
        self._validate_trigger(trigger)

        # trigger mode must be set first and on its own!
        await self._drv.trigger_mode.set(TetrammTrigger.ExtTrigger)

        await asyncio.gather(
            self._drv.averaging_time.set(exposure), self.set_frame_time(exposure)
        )

        status = await set_and_wait_for_value(self._drv.acquire, 1)

        return status

    def _validate_trigger(self, trigger: DetectorTrigger) -> None:
        supported_trigger_types = {
            DetectorTrigger.edge_trigger,
            DetectorTrigger.constant_gate,
        }

        if trigger not in supported_trigger_types:
            raise ValueError(
                f"{self.__class__.__name__} only supports the following trigger "
                f"types: {supported_trigger_types} but was asked to "
                f"use {trigger}"
            )

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
                f"frame_time {frame_time} is too low to collect at least "
                f"{self.minimum_values_per_reading} values per reading, at "
                f"{self.readings_per_frame} readings per frame."
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
        """Smallest amount of time needed to take a frame"""
        time_per_reading = self.minimum_values_per_reading / self.base_sample_rate
        return self.readings_per_frame * time_per_reading

    @minimum_frame_time.setter
    def minimum_frame_time(self, frame: float):
        time_per_reading = self.minimum_values_per_reading / self.base_sample_rate
        self.readings_per_frame = int(
            min(self.maximum_readings_per_frame, frame / time_per_reading)
        )


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
                self.drv.sample_time,
            ],
            name,
        )

    @property
    def hints(self) -> Hints:
        return {"fields": [self.name]}
