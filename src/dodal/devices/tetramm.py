from typing import Annotated as A

from ophyd_async.core import (
    AsyncStatus,
    DetectorTriggerLogic,
    PathProvider,
    SignalDict,
    SignalR,
    SignalRW,
    StandardDetector,
    StrictEnum,
    TriggerInfo,
    derived_signal_r,
    non_zero,
    wait_for_value,
)
from ophyd_async.epics.adcore import (
    ADArmLogic,
    ADHDFDataLogic,
    NDArrayBaseIO,
    NDArrayDescription,
    NDFileHDF5IO,
    NDPluginBaseIO,
)
from ophyd_async.epics.core import EpicsOptions, PvSuffix, epics_signal_r

from dodal.log import LOGGER


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


class TetrammDriver(NDArrayBaseIO):
    """Unlike other area detectors the tetramm driver does not inherit from ADBaseIO,
    see https://github.com/epics-modules/quadEM/tree/master.
    """

    acquire: A[SignalRW[bool], PvSuffix.rbv("Acquire"), EpicsOptions(wait=non_zero)]
    range = A[SignalRW[TetrammRange], PvSuffix.rbv("Range")]
    sample_time: A[SignalR[float], PvSuffix("SampleTime_RBV")]
    values_per_reading: A[SignalRW[int], PvSuffix.rbv("ValuesPerRead")]
    averaging_time: A[SignalRW[float], PvSuffix.rbv("AveragingTime")]
    to_average: A[SignalR[int], PvSuffix("NumAverage_RBV")]
    averaged: A[SignalR[int], PvSuffix("NumAveraged_RBV")]
    overflows: A[SignalR[int], PvSuffix("RingOverflows")]
    num_channels: A[SignalRW[TetrammChannels], PvSuffix.rbv("NumChannels")]
    resolution: A[SignalRW[TetrammResolution], PvSuffix.rbv("Resolution")]
    trigger_mode: A[SignalRW[TetrammTrigger], PvSuffix.rbv("TriggerMode")]
    bias: A[SignalRW[bool], PvSuffix.rbv("BiasState")]
    bias_volts: A[SignalRW[float], PvSuffix.rbv("BiasVoltage")]
    geometry: A[SignalRW[TetrammGeometry], PvSuffix.rbv("Geometry")]
    read_format: A[SignalRW[bool], PvSuffix.rbv("ReadFormat")]


class TetrammTriggerLogic(DetectorTriggerLogic):
    _base_sample_rate = 100_000
    _minimal_values_per_reading = {0: 5, 1: 500}

    def __init__(self, driver: TetrammDriver, file_io: NDFileHDF5IO):
        self.driver = driver
        self.file_io = file_io

    def get_deadtime(self, config_values) -> float:
        return 2 / self._base_sample_rate

    async def prepare_edge(self, num: int, livetime: float):
        await self.driver.trigger_mode.set(TetrammTrigger.EXT_TRIGGER)
        await self.set_exposure(livetime)

    async def prepare_level(self, num: int):
        await self.driver.trigger_mode.set(TetrammTrigger.EXT_TRIGGER)

    async def set_exposure(self, exposure: float):
        sample_time = await self.driver.sample_time.get_value()

        minimum_samples = self._minimal_values_per_reading[
            await self.driver.read_format.get_value()
        ]

        samples = int(exposure / sample_time)

        if samples < minimum_samples:
            raise ValueError(
                "Tetramm exposure time must be at least "
                f"{minimum_samples * sample_time}s, asked to set it to {exposure}s"
            )

        await self.driver.averaging_time.set(samples * sample_time)


class TetrammArmLogic(ADArmLogic):
    def __init__(self, driver: NDArrayBaseIO, writer_acquire: SignalRW):
        self.writer_acquire = writer_acquire
        super().__init__(driver)

    async def wait_for_idle(self):
        await wait_for_value(self.writer_acquire, False, timeout=None)

    async def disarm(self, on_unstage: bool):
        await super().disarm(on_unstage)
        if self.acquire_status:
            await self.acquire_status


class TetrammDetector(StandardDetector):
    """Unlike other AreaDetectors the tetramm driver does not internally stop after the
    expected number of triggers, instead we set the expected number of frames on the file
    writer, which will then internally stop when it receives this number of frames, and
    we rely on this stopping to know the detector is done.
    """

    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        drv_suffix: str = "DRV:",
        fileio_suffix: str = "HDF5:",
        plugins: dict[str, NDPluginBaseIO] | None = None,
        name: str = "",
    ):
        self.driver = TetrammDriver(prefix + drv_suffix)
        self.file_io = NDFileHDF5IO(prefix + fileio_suffix)

        if plugins is None:
            plugins = {}

        for plugin_name, plugin in plugins.items():
            setattr(self, plugin_name, plugin)

        def _get_num_channels(num_channels: TetrammChannels) -> int:
            return int(num_channels)

        self.num_channels = derived_signal_r(
            _get_num_channels, num_channels=self.driver.num_channels
        )

        super().__init__(name=name)

        self.add_detector_logics(
            ADHDFDataLogic(
                writer=self.file_io,
                driver=self.driver,
                path_provider=path_provider,
                description=NDArrayDescription(
                    shape_signals=[self.num_channels, self.driver.to_average],
                    data_type_signal=self.driver.data_type,
                    color_mode_signal=self.driver.color_mode,
                ),
                plugins=list(plugins.values()),
            ),
            TetrammTriggerLogic(self.driver, self.file_io),
            TetrammArmLogic(self.driver, self.file_io.capture),
        )

        # currents
        self.current1 = epics_signal_r(float, prefix + "Cur1:MeanValue_RBV")
        self.current2 = epics_signal_r(float, prefix + "Cur2:MeanValue_RBV")
        self.current3 = epics_signal_r(float, prefix + "Cur3:MeanValue_RBV")
        self.current4 = epics_signal_r(float, prefix + "Cur4:MeanValue_RBV")

        # configuration signals
        self.add_config_signals(
            self.driver.values_per_reading,
            self.driver.averaging_time,
            self.driver.sample_time,
        )

    @AsyncStatus.wrap
    async def prepare(self, value: TriggerInfo):
        current_trig_status = await self.driver.trigger_mode.get_value()
        if (
            current_trig_status == TetrammTrigger.FREE_RUN
            and self._arm_logic is not None
        ):  # if freerun turn off first
            LOGGER.info("Disarming TetrAMM from free run")
            await self._arm_logic.disarm(on_unstage=False)
        await super().prepare(value)
        # Standard detector sets this to 0 in prepare, we must set it to the correct
        # number here as it is used as a proxy to know when we're done
        await self.file_io.num_capture.set(value.number_of_exposures)
        self._validate_deadtime(value)

    def _validate_deadtime(self, value: TriggerInfo) -> None:
        if self._trigger_logic is None:
            raise RuntimeError("")
        minimum_deadtime = self._trigger_logic.get_deadtime(SignalDict())
        if minimum_deadtime > value.deadtime:
            msg = (
                f"Tetramm {self} needs at least {minimum_deadtime}s "
                f"deadtime, but trigger logic provides only {value.deadtime}s"
            )
            raise ValueError(msg)
