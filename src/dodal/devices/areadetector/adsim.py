from bluesky.protocols import HasHints, Hints
from ophyd_async.core import (
    PathProvider,
    StandardDetector,
)
from ophyd_async.epics.adcore import (
    ADBaseDatasetDescriber,
    ADBaseIO,
    ADHDFWriter,
    NDFileHDFIO,
    NDPluginStatsIO,
)
from ophyd_async.epics.adsimdetector import SimController


class AdSimDetector(StandardDetector, HasHints):
    """
    Ophyd-async implementation of the SimAreaDetector
    """

    def __init__(
        self,
        name: str,
        prefix: str,
        directory_provider: PathProvider,
    ):
        drv = ADBaseIO(prefix + "CAM:")
        hdf = NDFileHDFIO(prefix + "HDF5:")

        self.drv = drv
        self.hdf = hdf
        self.stats = NDPluginStatsIO(prefix + "STAT:")

        super().__init__(
            SimController(drv),
            ADHDFWriter(
                hdf,
                directory_provider,
                lambda: self.name,
                ADBaseDatasetDescriber(drv),
            ),
            config_sigs=[drv.acquire_time, drv.acquire],
            name=name,
        )

    @property
    def hints(self) -> Hints:
        assert isinstance(self.writer, ADHDFWriter)
        return self.writer.hints
