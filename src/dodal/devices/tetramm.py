import asyncio

from bluesky.protocols import Hints
from ophyd_async.core import (
    DatasetDescriber,
    DetectorController,
    DetectorTrigger,
    Device,
    PathProvider,
    StandardDetector,
    StrictEnum,
    TriggerInfo,
    set_and_wait_for_value,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.adcore import (
    ADHDFWriter,
    NDFileHDFIO,
    NDPluginBaseIO,
    stop_busy_record,
)
from ophyd_async.epics.core import (
    epics_signal_r,
    epics_signal_rw,
    epics_signal_rw_rbv,
)


class TetrammRange(StrictEnum):
    UA = "+- 120 uA"
    NA = "+- 120 nA"


class TetrammTrigger(StrictEnum):
    FREE_RUN = "Free run"
    EXT_TRIGGER = "Ext. trig."
    EXT_BULB = "Ext. bulb"
    EXT_GATE = "Ext. gate"


class TetrammChannels(StrictEnum):
    ONE = "1"
    TWO = "2"
    FOUR = "4"


class TetrammResolution(StrictEnum):
    SIXTEEN_BITS = "16 bits"
    TWENTY_FOUR_BITS = "24 bits"


class TetrammGeometry(StrictEnum):
    DIAMOND = "Diamond"
    SQUARE = "Square"


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


class TetrammController(DetectorController):
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

    def get_deadtime(self, exposure: float | None) -> float:
        # 2 internal clock cycles. Best effort approximation
        return 2 / self.base_sample_rate

    async def prepare(self, trigger_info: TriggerInfo):
        self._validate_trigger(trigger_info.trigger)
        assert trigger_info.livetime is not None

        # trigger mode must be set first and on its own!
        await self._drv.trigger_mode.set(TetrammTrigger.EXT_TRIGGER)

        await asyncio.gather(
            self._drv.averaging_time.set(trigger_info.livetime),
            self.set_exposure(trigger_info.livetime),
        )

    async def arm(self):
        self._arm_status = await set_and_wait_for_value(
            self._drv.acquire, True, wait_for_set_completion=False
        )

    async def wait_for_idle(self):
        if self._arm_status and not self._arm_status.done:
            await self._arm_status
        self._arm_status = None

    def _validate_trigger(self, trigger: DetectorTrigger) -> None:
        supported_trigger_types = {
            DetectorTrigger.EDGE_TRIGGER,
            DetectorTrigger.CONSTANT_GATE,
        }

        if trigger not in supported_trigger_types:
            raise ValueError(
                f"{self.__class__.__name__} only supports the following trigger "
                f"types: {supported_trigger_types} but was asked to "
                f"use {trigger}"
            )

    async def disarm(self):
        await stop_busy_record(self._drv.acquire, False, timeout=1)

    async def set_exposure(self, exposure: float):
        """Tries to set the exposure time of a single frame.

        As during the  exposure time, the device must collect an integer number
        of readings, in the case where the exposure is not a multiple of the base
        sample rate, it will be lowered to the prior multiple ot ensure triggers
        are not missed.

        Args:
            exposure (float): The time for a single frame in seconds

        Raises:
            ValueError: If exposure is too low to collect the required number
            of readings per frame.
        """

        # Set up the number of readings across the exposure period to scale with
        # the exposure time
        self._set_minimum_exposure(exposure)
        values_per_reading: int = int(
            exposure * self.base_sample_rate / self.readings_per_frame
        )

        await self._drv.values_per_reading.set(values_per_reading)

    @property
    def max_frame_rate(self) -> float:
        """Max frame rate in Hz for the current configuration"""
        return 1 / self.minimum_exposure

    @max_frame_rate.setter
    def max_frame_rate(self, mfr: float):
        self._set_minimum_exposure(1 / mfr)

    @property
    def minimum_exposure(self) -> float:
        """Smallest amount of time needed to take a frame"""
        time_per_reading = self.minimum_values_per_reading / self.base_sample_rate
        return self.readings_per_frame * time_per_reading

    def _set_minimum_exposure(self, exposure: float):
        time_per_reading = self.minimum_values_per_reading / self.base_sample_rate
        if exposure < time_per_reading:
            raise ValueError(
                "Tetramm exposure time must be at least "
                f"{time_per_reading}s, asked to set it to {exposure}s"
            )
        self.readings_per_frame = int(
            min(self.maximum_readings_per_frame, exposure / time_per_reading)
        )


class TetrammDatasetDescriber(DatasetDescriber):
    max_channels = 11

    def __init__(self, controller: TetrammController) -> None:
        self.controller = controller

    async def np_datatype(self) -> str:
        return "<f8"  # IEEE 754 double precision floating point

    async def shape(self) -> tuple[int, int]:
        return (self.max_channels, self.controller.readings_per_frame)


# TODO: Support MeanValue signals https://github.com/DiamondLightSource/dodal/issues/337
class TetrammDetector(StandardDetector):
    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        name: str = "",
        type: str | None = None,
        plugins: dict[str, NDPluginBaseIO] | None = None,
    ) -> None:
        self.drv = TetrammDriver(prefix + "DRV:")
        self.hdf = NDFileHDFIO(prefix + "HDF5:")
        controller = TetrammController(self.drv)
        config_signals = [
            self.drv.values_per_reading,
            self.drv.averaging_time,
            self.drv.sample_time,
        ]
        if type:
            self.type, _ = soft_signal_r_and_setter(str, type)
            config_signals.append(self.type)
        else:
            self.type = None
        super().__init__(
            controller,
            ADHDFWriter(
                fileio=self.hdf,
                path_provider=path_provider,
                dataset_describer=TetrammDatasetDescriber(controller),
                plugins=plugins,
            ),
            config_signals,
            name,
        )

    @property
    def hints(self) -> Hints:
        return {"fields": [self.name]}
