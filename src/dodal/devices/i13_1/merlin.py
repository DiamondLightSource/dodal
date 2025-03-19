from ophyd_async.core import PathProvider, StandardDetector
from ophyd_async.epics import adcore

from dodal.common.beamlines.device_helpers import CAM_SUFFIX, HDF5_SUFFIX
from dodal.devices.i13_1.merlin_controller import MerlinController
from dodal.devices.i13_1.merlin_io import MerlinDriverIO


class Merlin(StandardDetector):
    _controller: MerlinController
    _writer: adcore.ADHDFWriter

    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        drv_suffix=CAM_SUFFIX,
        fileio_suffix=HDF5_SUFFIX,
        name: str = "",
    ):
        self.drv = MerlinDriverIO(prefix + drv_suffix)
        self.hdf = adcore.NDFileHDFIO(prefix + fileio_suffix)

        super().__init__(
            MerlinController(self.drv),
            adcore.ADHDFWriter(
                self.hdf,
                path_provider,
                lambda: self.name,
                adcore.ADBaseDatasetDescriber(self.drv),
            ),
            config_sigs=(self.drv.acquire_period, self.drv.acquire_time),
            name=name,
        )
