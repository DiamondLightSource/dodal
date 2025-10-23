import asyncio
from collections.abc import AsyncGenerator, AsyncIterator
from pathlib import Path

from bluesky.protocols import StreamAsset
from event_model import DataKey  # type: ignore
from ophyd_async.core import (
    AsyncStatus,
    AutoIncrementingPathProvider,
    DetectorWriter,
    StandardDetector,
    StandardReadable,
    StaticPathProvider,
    TriggerInfo,
    observe_value,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_rw_rbv
from ophyd_async.fastcs.jungfrau._controller import JungfrauController
from ophyd_async.fastcs.jungfrau._signals import JungfrauDriverIO

from dodal.log import LOGGER


class JunfrauCommissioningWriter(DetectorWriter, StandardReadable):
    """Implementation of the temporary filewriter used for Jungfrau commissioning on i24.

    The PVs on this device are responsible for writing files of a specified name
    to a specified path, marking itself as "ready to write", and having a counter of
    frames written, which must be zero'd at the ophyd level
    """

    def __init__(
        self,
        prefix,
        path_provider: AutoIncrementingPathProvider | StaticPathProvider,
        name="",
    ) -> None:
        with self.add_children_as_readables():
            self._path_info = path_provider
            self.frame_counter = epics_signal_rw(int, f"{prefix}NumCaptured")
            self.file_name = epics_signal_rw_rbv(str, f"{prefix}FileName")
            self.file_path = epics_signal_rw_rbv(str, f"{prefix}FilePath")
            self.writer_ready = epics_signal_r(int, f"{prefix}Ready_RBV")
            self.expected_frames = epics_signal_rw(int, f"{prefix}NumCapture")
        super().__init__(name)

    async def open(self, name: str, exposures_per_event: int = 1) -> dict[str, DataKey]:
        self._exposures_per_event = exposures_per_event
        _path_info = self._path_info()

        # Commissioning Jungfrau plans allow you to override path, so check to see if file exists
        requested_filepath = Path(_path_info.directory_path) / _path_info.filename
        if requested_filepath.exists():
            raise FileExistsError(
                f"Jungfrau was requested to write to {requested_filepath}, but this file already exists!"
            )

        await asyncio.gather(
            self.file_name.set(_path_info.filename),
            self.file_path.set(str(_path_info.directory_path)),
            self.frame_counter.set(0),
        )
        LOGGER.info(
            f"Jungfrau writing to folder {_path_info.directory_path} with filename {_path_info.filename}"
        )
        await wait_for_value(self.writer_ready, 1, timeout=10)
        return await self._describe()

    async def _describe(self) -> dict[str, DataKey]:
        # Dummy function, doesn't actually describe the dataset

        return {
            "data": DataKey(
                source="Commissioning writer",
                shape=[-1],
                dtype="array",
                dtype_numpy="<u2",
                external="STREAM:",
            )
        }

    async def observe_indices_written(
        self, timeout: float
    ) -> AsyncGenerator[int, None]:
        timeout = timeout * 4  # This filewriter is very slow
        async for num_captured in observe_value(self.frame_counter, timeout):
            yield num_captured // (self._exposures_per_event)

    async def get_indices_written(self) -> int:
        return await self.frame_counter.get_value() // self._exposures_per_event

    def collect_stream_docs(
        self, name: str, indices_written: int
    ) -> AsyncIterator[StreamAsset]:
        raise NotImplementedError()

    async def close(self) -> None: ...


class CommissioningJungfrau(
    StandardDetector[JungfrauController, JunfrauCommissioningWriter]
):
    """Ophyd-async implementation of a Jungfrau 9M Detector, using a temporary
    filewriter in place of Odin"""

    def __init__(
        self,
        prefix: str,
        writer_prefix: str,
        path_provider: AutoIncrementingPathProvider | StaticPathProvider,
        name="",
    ):
        self.drv = JungfrauDriverIO(prefix)
        writer = JunfrauCommissioningWriter(writer_prefix, path_provider)
        controller = JungfrauController(self.drv)
        super().__init__(controller, writer, name=name)

    @AsyncStatus.wrap
    async def prepare(self, value: TriggerInfo) -> None:
        await super().prepare(value)
        await self._writer.expected_frames.set(value.total_number_of_exposures)
