from bluesky.protocols import HasHints, Hints
from ophyd_async.core import (
    DirectoryProvider,
    StandardDetector,
)
from ophyd_async.epics.areadetector.controllers import ADSimController
from ophyd_async.epics.areadetector.drivers import ADBase, ADBaseShapeProvider
from ophyd_async.epics.areadetector.writers import HDFWriter, NDFileHDF, NDPluginStats


class AdSimDetector(StandardDetector, HasHints):
    """
    Ophyd-async implementation of the SimAreaDetector
    """

    def __init__(
        self,
        name: str,
        prefix: str,
        directory_provider: DirectoryProvider,
    ):
        drv = ADBase(prefix + "CAM:")
        hdf = NDFileHDF(prefix + "HDF5:")

        self.drv = drv
        self.hdf = hdf
        self.stats = NDPluginStats(prefix + "STAT:")

        super().__init__(
            ADSimController(drv),
            HDFWriter(
                hdf,
                directory_provider,
                lambda: self.name,
                ADBaseShapeProvider(drv),
                sum="StatsTotal",
            ),
            config_sigs=[drv.acquire_time, drv.acquire],
            name=name,
        )

    @property
    def hints(self) -> Hints:
        assert isinstance(self.writer, HDFWriter)
        return self.writer.hints
