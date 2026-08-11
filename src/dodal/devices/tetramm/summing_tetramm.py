import asyncio
from math import ceil
from typing import Annotated as A
from typing import override

from ophyd_async.core import (
    AsyncStatus,
    DetectorTriggerLogic,
    EnableDisable,
    PathProvider,
    SignalR,
    SignalRW,
    TriggerInfo,
)
from ophyd_async.core._signal import soft_signal_r_and_setter
from ophyd_async.epics.adcore import (
    NDPluginBaseIO,
)
from ophyd_async.epics.core import PvSuffix

from dodal.devices.tetramm.tetramm import (
    TetrammDetector,
    TetrammTriggerLogic,
)

## See https://github.com/bluesky/ophyd-async/issues/1390 for adding these into `ophyd-async`


class NDROIIO(NDPluginBaseIO):
    """Plugin for taking a region of an NDArray.

    This mirrors the interface provided by ADCore/db/NDROI.template.
    See HTML docs at https://areadetector.github.io/areaDetector/ADCore/NDPluginROI.html
    """

    size_x: A[SignalRW[int], PvSuffix.rbv("SizeX")]
    size_y: A[SignalRW[int], PvSuffix.rbv("SizeY")]
    size_z: A[SignalRW[int], PvSuffix.rbv("SizeZ")]

    bin_x: A[SignalRW[int], PvSuffix.rbv("BinX")]
    bin_y: A[SignalRW[int], PvSuffix.rbv("BinY")]
    bin_z: A[SignalRW[int], PvSuffix.rbv("BinZ")]


class NDProc(NDPluginBaseIO):
    """Plugin for performing processing on an NDArrray.

    This mirrors the interface provided by ADCore/db/NDProcess.template.
    See HTML docs at https://areadetector.github.io/areaDetector/ADCore/NDPluginProcess.html
    """

    enable_scale: A[SignalRW[EnableDisable], PvSuffix.rbv("EnableOffsetScale")]
    scale: A[SignalRW[float], PvSuffix.rbv("Scale")]


class SummingTetrammTriggerLogic(TetrammTriggerLogic):
    async def prepare_edge(self, num: int, livetime: float):
        await self.set_values_per_reading(livetime)
        await super().prepare_edge(num, livetime)

    async def set_values_per_reading(self, exposure: float):
        """Set the values per reading so that the device produces as much data as
        possible.

        Setting to more than 10 times exposure overloads the device's internal buffers.
        """
        minimum_values_per_reading = await self.minimum_values_per_reading()

        smallest_values_per_reading = max(
            minimum_values_per_reading, ceil(10 * exposure)
        )
        await self.driver.values_per_reading.set(smallest_values_per_reading)


class SummingTetrammDetector(TetrammDetector):
    """When triggered the tetramm will average a number of readings from the hardware
    (as defined by values per reading and averaging time) and produce a reading at each
    sample time. It will also do this for all its channels. Scientifically, we're using
    the tetramm as a proxy for flux so what we would like is a single sum of the data
    from all channels across the whole exposure time. The specific units that this sum
    is in do not matter as long as they are consistent between frames and between collections.

    This device uses an AD chain to provide this sum with the following logic:
    1. Take the raw values into the stats plugin to provide a sum of the 4 channels
    2. Use an ROI plugin to add all the values across the whole exposure time
    3. Use the process plugin to multiple this all by the values per reading, this makes
       the number independent of the sampling time used for averaging internally in the
       device
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
        if plugins is None:
            plugins = {}

        self.stats = NDPluginBaseIO(f"{prefix}SumAll:")
        self.proc1 = NDProc(f"{prefix}PROC1:")
        self.roi = NDROIIO(f"{prefix}ROI:")

        plugins.update(
            {
                "stats": self.stats,
                "proc1": self.proc1,
                "roi": self.roi,
            }
        )

        self._shape_of_one, _ = soft_signal_r_and_setter(int, 1)

        super().__init__(
            prefix, path_provider, drv_suffix, fileio_suffix, plugins, name
        )

    @override
    def get_shape(self) -> list[SignalR]:
        return [self._shape_of_one]

    @override
    def get_detector_trigger_logic(self) -> DetectorTriggerLogic:
        return SummingTetrammTriggerLogic(self.driver, self.file_io)

    @AsyncStatus.wrap
    async def prepare(self, value: TriggerInfo):
        """Ensure the AD plugin chain, and settings are configured as described in the
        class docstring.
        """
        await super().prepare(value)

        roi_port = await self.roi.port_name.get_value()
        proc1_port = await self.proc1.port_name.get_value()
        stats_port = await self.stats.port_name.get_value()

        await asyncio.gather(
            self.roi.nd_array_port.set(stats_port),
            self.proc1.nd_array_port.set(roi_port),
            self.file_io.nd_array_port.set(proc1_port),
        )

        await self.proc1.enable_scale.set(EnableDisable.ENABLE)

        values_per_reading = await self.driver.values_per_reading.get_value()
        to_average = await self.driver.to_average.get_value()
        await asyncio.gather(
            self.roi.size_x.set(to_average),
            self.roi.bin_x.set(to_average),
            self.proc1.scale.set(values_per_reading),
        )
