from bluesky.protocols import Hints
from ophyd_async.core import PathProvider, StandardDetector
from ophyd_async.epics.adcore import ADBaseDatasetDescriber, ADHDFWriter, NDFileHDFIO

from dodal.devices.areadetector.andor2_epics import Andor2Controller, Andor2DriverIO


class Andor2(StandardDetector):
    """
    Andor 2 area detector device (CCD detector 56fps with full chip readout).
    Andor model:DU897_BV.
    """

    _controller: Andor2Controller
    _writer: ADHDFWriter

    def __init__(
        self,
        prefix: str,
        path_provider: PathProvider,
        name: str,
    ):
        """
        Parameters
        ----------
        prefix: str
            Epic Pv,
        path_provider: PathProvider
            Path provider for hdf writer
        name: str
            Name of the device
        """
        self.drv = Andor2DriverIO(prefix + "CAM:")
        self.hdf = NDFileHDFIO(prefix + "HDF5:")
        super().__init__(
            Andor2Controller(self.drv),
            ADHDFWriter(
                hdf=self.hdf,
                path_provider=path_provider,
                name_provider=lambda: self.name,
                dataset_describer=ADBaseDatasetDescriber(self.drv),
            ),
            config_sigs=[self.drv.acquire_time],
            name=name,
        )

    @property
    def hints(self) -> Hints:
        return self._writer.hints
