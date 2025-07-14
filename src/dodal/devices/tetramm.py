import asyncio
from collections.abc import Sequence
from typing import Annotated as A

from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    DatasetDescriber,
    DetectorController,
    DetectorTrigger,
    PathProvider,
    SignalR,
    SignalRW,
    StandardDetector,
    StrictEnum,
    TriggerInfo,
    set_and_wait_for_value,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.adcore import (
    ADHDFWriter,
    NDArrayBaseIO,
    NDFileHDFIO,
    NDPluginBaseIO,
    stop_busy_record,
)
from ophyd_async.epics.core import PvSuffix


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


class TetrammController(DetectorController):
    """Controller for a TetrAMM current monitor"""

    _supported_trigger_types = {
        DetectorTrigger.EDGE_TRIGGER: TetrammTrigger.EXT_TRIGGER,
        DetectorTrigger.CONSTANT_GATE: TetrammTrigger.EXT_TRIGGER,
    }
    """"On the TetrAMM ASCII mode requires a minimum value of ValuesPerRead of 500,
    [...] binary mode the minimum value of ValuesPerRead is 5."
    https://millenia.cars.aps.anl.gov/software/epics/quadEMDoc.html
    """
    _minimal_values_per_reading = {0: 5, 1: 500}
    """The TetrAMM always digitizes at 100 kHz"""
    _base_sample_rate: int = 100_000

    def __init__(
        self,
        driver: TetrammDriver,
    ) -> None:
        self.driver = driver
        self._arm_status: AsyncStatus | None = None

    def get_deadtime(self, exposure: float | None) -> float:
        # 2 internal clock cycles. Best effort approximation
        return 2 / self._base_sample_rate

    async def prepare(self, trigger_info: TriggerInfo) -> None:
        if trigger_info.trigger not in self._supported_trigger_types:
            raise TypeError(
                f"{self.__class__.__name__} only supports the following trigger "
                f"types: {[k.name for k in self._supported_trigger_types]} but was asked to "
                f"use {trigger_info.trigger}"
            )
        if trigger_info.livetime is None:
            raise ValueError(f"{self.__class__.__name__} requires that livetime is set")

        # trigger mode must be set first and on its own!
        await self.driver.trigger_mode.set(
            self._supported_trigger_types[trigger_info.trigger]
        )
        await asyncio.gather(
            self.driver.averaging_time.set(trigger_info.livetime),
            self.set_exposure(trigger_info.livetime),
        )

    async def arm(self):
        self._arm_status = await self.start_acquiring_driver_and_ensure_status()

    async def wait_for_idle(self):
        if self._arm_status and not self._arm_status.done:
            await self._arm_status
        self._arm_status = None

    async def disarm(self):
        # We can't use caput callback as we already used it in arm() and we can't have
        # 2 or they will deadlock
        await stop_busy_record(self.driver.acquire, False, timeout=1)

    async def set_exposure(self, exposure: float) -> None:
        """Set the exposure time and acquire period.

        As during the  exposure time, the device must collect an integer number
        of readings, in the case where the exposure is not a multiple of the base
        sample rate, it will be lowered to the prior multiple ot ensure triggers
        are not missed.

        :param exposure: Desired exposure time.
        :type exposure: How long to wait for the exposure time and acquire
            period to be set.
        """
        sample_time = await self.driver.sample_time.get_value()
        minimum_samples = self._minimal_values_per_reading[
            await self.driver.read_format.get_value()
        ]
        samples_per_reading = int(exposure / sample_time)
        if samples_per_reading < minimum_samples:
            raise ValueError(
                "Tetramm exposure time must be at least "
                f"{minimum_samples * sample_time}s, asked to set it to {exposure}s"
            )
        await self.driver.averaging_time.set(samples_per_reading * sample_time)

    async def start_acquiring_driver_and_ensure_status(self) -> AsyncStatus:
        """Start acquiring driver, raising ValueError if the detector is in a bad state.

        This sets driver.acquire to True, and waits for it to be True up to a timeout.
        Then, it checks that the DetectorState PV is in DEFAULT_GOOD_STATES,
        and otherwise raises a ValueError.

        :returns AsyncStatus:
            An AsyncStatus that can be awaited to set driver.acquire to True and perform
            subsequent raising (if applicable) due to detector state.
        """
        status = await set_and_wait_for_value(
            self.driver.acquire,
            True,
            timeout=DEFAULT_TIMEOUT,
            wait_for_set_completion=False,
        )

        async def complete_acquisition() -> None:
            # NOTE: possible race condition here between the callback from
            # set_and_wait_for_value and the detector state updating.
            await status

        return AsyncStatus(complete_acquisition())


class TetrammDatasetDescriber(DatasetDescriber):
    def __init__(self, driver: TetrammDriver) -> None:
        self._driver = driver

    async def np_datatype(self) -> str:
        return "<f8"  # IEEE 754 double precision floating point

    async def shape(self) -> tuple[int, int]:
        return (
            int(await self._driver.num_channels.get_value()),
            int(
                await self._driver.averaging_time.get_value()
                / await self._driver.sample_time.get_value(),
            ),
        )


class TetrammDetector(StandardDetector):
    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        drv_suffix: str = "DRV:",
        fileio_suffix: str = "HDF5:",
        name: str = "",
        plugins: dict[str, NDPluginBaseIO] | None = None,
        config_sigs: Sequence[SignalR] = (),
        type: str | None = None,
    ):
        self.driver = TetrammDriver(prefix + drv_suffix)
        self.file_io = NDFileHDFIO(prefix + fileio_suffix)
        controller = TetrammController(self.driver)

        writer = ADHDFWriter(
            fileio=self.file_io,
            path_provider=path_provider,
            dataset_describer=TetrammDatasetDescriber(self.driver),
            plugins=plugins,
        )

        config_sigs = [
            self.driver.values_per_reading,
            self.driver.averaging_time,
            self.driver.sample_time,
            *config_sigs,
        ]

        if type:
            self.type, _ = soft_signal_r_and_setter(str, type)
            config_sigs.append(self.type)
        else:
            self.type = None

        if plugins is not None:
            for plugin_name, plugin in plugins.items():
                setattr(self, plugin_name, plugin)

        super().__init__(
            controller=controller,
            writer=writer,
            name=name,
            config_sigs=config_sigs,
        )
