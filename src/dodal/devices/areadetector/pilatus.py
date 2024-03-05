from typing import Sequence

from bluesky.protocols import Hints
from ophyd_async.core import DirectoryProvider, SignalR, StandardDetector
from ophyd_async.epics.areadetector.controllers import PilatusController
from ophyd_async.epics.areadetector.drivers import ADBaseShapeProvider, PilatusDriver
from ophyd_async.epics.areadetector.writers import HDFWriter, NDFileHDF, NDPluginStats


class HDFStatsPilatus(StandardDetector):
    _controller: PilatusController
    _writer: HDFWriter

    def __init__(
        self,
        prefix: str,
        directory_provider: DirectoryProvider,
        name: str,
        config_sigs: Sequence[SignalR] = (),
        **scalar_sigs: str,
    ):
        self.drv = PilatusDriver(prefix + "CAM:")
        self.hdf = NDFileHDF(prefix + "HDF5:")
        self.stats = NDPluginStats(prefix + "STAT:")

        super().__init__(
            PilatusController(self.drv),
            HDFWriter(
                self.hdf,
                directory_provider,
                lambda: self.name,
                ADBaseShapeProvider(self.drv),
                sum="StatsTotal",
                **scalar_sigs,
            ),
            config_sigs=config_sigs,
            name=name,
        )

    @property
    def hints(self) -> Hints:
        return self.writer.hints
