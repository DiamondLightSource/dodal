from bluesky.protocols import Hints
from ophyd_async.core import PathProvider, StandardDetector
from ophyd_async.epics.adcore import ADBaseDatasetDescriber, ADHDFWriter, NDFileHDFIO

from dodal.devices.areadetector.andor2_epics import Andor2Controller, Andor2DriverIO


class Andor2(StandardDetector):
    """
    Andor 2 area detector device

    Parameters
    ----------
    prefix: str
        Epic Pv,
    path_provider: PathProvider
        Path provider for hdf writer
    name: str
        Name of the device
    config_sigs: Sequence[SignalR]
        optional config signal to be added
    **scalar_sigs: str
        Optional scalar signals
    """

    _controller: Andor2Controller
    _writer: ADHDFWriter

    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        name: str,
    ):
        self.drv = Andor2DriverIO(prefix + "CAM:")
        self.hdf = NDFileHDFIO(prefix + "HDF5:")
        super().__init__(
            Andor2Controller(self.drv),
            ADHDFWriter(
                self.hdf,
                path_provider,
                lambda: self.name,
                ADBaseDatasetDescriber(self.drv),
            ),
            config_sigs=[self.drv.acquire_time],
            name=name,
        )

    @property
    def hints(self) -> Hints:
        return self._writer.hints
