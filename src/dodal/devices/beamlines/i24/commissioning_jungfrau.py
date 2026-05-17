import asyncio
from pathlib import Path

from ophyd_async.core import (
    AsyncStatus,
    DetectorDataLogic,
    PathProvider,
    StandardDetector,
    StandardReadable,
    StreamableDataProvider,
    StreamResourceDataProvider,
    StreamResourceInfo,
    TriggerInfo,
    soft_signal_r_and_setter,
    soft_signal_rw,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_r, epics_signal_rw, epics_signal_rw_rbv
from ophyd_async.fastcs.core import fastcs_connector
from ophyd_async.fastcs.jungfrau._arm_logic import JungfrauArmLogic
from ophyd_async.fastcs.jungfrau._io import AcquisitionType, JungfrauDriverIO
from ophyd_async.fastcs.jungfrau._trigger_logic import JungfrauTriggerLogic

from dodal.log import LOGGER


class JungfrauCommissioningWriter(StandardReadable):
    """Implementation of the temporary filewriter used for Jungfrau commissioning on i24.

    The PVs on this device are responsible for writing files of a specified name
    to a specified path, marking itself as "ready to write", and having a counter of
    frames written, which must be zero'd at the ophyd level.
    """

    def __init__(
        self,
        prefix,
        name="",
    ) -> None:
        with self.add_children_as_readables():
            self.frame_counter = epics_signal_rw(int, f"{prefix}NumCaptured")
            self.file_name = epics_signal_rw_rbv(str, f"{prefix}FileName")
            self.file_path = epics_signal_rw_rbv(str, f"{prefix}FilePath")
            self.writer_ready = epics_signal_r(int, f"{prefix}Ready_RBV")
            self.expected_frames = epics_signal_rw(int, f"{prefix}NumCapture")
        super().__init__(name)


class JungfrauCommissioningWriterDataLogic(DetectorDataLogic):
    """Implementation of the temporary filewriter used for Jungfrau commissioning on i24.

    The PVs on this device are responsible for writing files of a specified name
    to a specified path, marking itself as "ready to write", and having a counter of
    frames written, which must be zero'd at the ophyd level.
    """

    def __init__(
        self,
        path_provider: PathProvider,
        writer: JungfrauCommissioningWriter,
    ) -> None:
        self.path_provider = path_provider
        self._writer = writer

    async def prepare_unbounded(self, datakey_name: str) -> StreamableDataProvider:
        # Work out where to write
        path_info = self.path_provider(datakey_name)

        # Setup the writer
        requested_filepath = Path(path_info.directory_path) / path_info.filename
        if requested_filepath.exists():
            raise FileExistsError(
                f"Jungfrau was requested to write to {requested_filepath}, but this file already exists!"
            )
        filename = f"{path_info.filename}.h5"
        await asyncio.gather(
            self._writer.file_name.set(path_info.filename),
            self._writer.file_path.set(str(path_info.directory_path)),
            self._writer.frame_counter.set(0),
        )

        LOGGER.info(
            f"Jungfrau writing to folder {path_info.directory_path} with filename {path_info.filename}"
        )

        await wait_for_value(self._writer.writer_ready, 1, timeout=10)

        # Return a provider that reflects what we have made
        data_shape = (-1,)
        resource = StreamResourceInfo(
            data_key=datakey_name,
            shape=data_shape,
            chunk_shape=(1, *data_shape),
            dtype_numpy="<u2",
            parameters={"dataset": "/data"},
        )
        return StreamResourceDataProvider(
            uri=f"{path_info.directory_uri}{filename}",
            resources=[resource],
            mimetype="application/x-hdf5",
            collections_written_signal=self._writer.frame_counter,
        )


class CommissioningJungfrauDetector(StandardDetector):
    """Ophyd-async implementation of a Jungfrau 9M Detector, using a temporary
    filewriter in place of Odin.

    Replace with the one inside ophyd-async once Odin is working.
    """

    def __init__(
        self,
        prefix: str,
        writer_prefix: str,
        path_provider: PathProvider,
        drv_suffix: str,
        name="",
        detector_id=124,
    ):
        drv_connector = fastcs_connector(prefix + drv_suffix)
        self.detector = JungfrauDriverIO(connector=drv_connector)
        drv_connector.create_children_from_annotations(self.detector)
        self.writer = JungfrauCommissioningWriter(writer_prefix)
        self.acquisition_type = soft_signal_rw(
            AcquisitionType, AcquisitionType.STANDARD
        )
        self.ispyb_detector_id, _ = soft_signal_r_and_setter(
            int,
            initial_value=detector_id,
        )
        self.add_detector_logics(
            JungfrauTriggerLogic(self.detector, self.acquisition_type),
            JungfrauArmLogic(self.detector),
            JungfrauCommissioningWriterDataLogic(path_provider, self.writer),
        )
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def prepare(self, value: TriggerInfo):
        await super().prepare(value)
        # Standard detector sets this to 0 in prepare, we must set it to the correct
        # number here as it is used as a proxy to know when we're done
        await self.writer.expected_frames.set(value.number_of_exposures)
