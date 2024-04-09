from typing import Sequence

from bluesky.protocols import Hints
from ophyd_async.core import DirectoryProvider, SignalR, StandardDetector
from ophyd_async.epics.areadetector.drivers import ADBaseShapeProvider
from ophyd_async.epics.areadetector.writers import HDFWriter, NDFileHDF, NDPluginStats

from dodal.devices.areadetector.epics.drivers.pimte1_driver import Pimte1Driver
from dodal.devices.areadetector.epics.pimte_controller import PimteController


class HDFStatsPimte(StandardDetector):
    _controller: PimteController
    _writer: HDFWriter

    def __init__(
        self,
        prefix: str,
        directory_provider: DirectoryProvider,
        name: str,
        config_sigs: Sequence[SignalR] = (),
        **scalar_sigs: str,
    ):
        self.drv = Pimte1Driver(prefix + "CAM:")
        self.hdf = NDFileHDF(prefix + "HDF5:")
        self.stats = NDPluginStats(prefix + "STAT:")
        # taken from i22 but this does nothing atm

        super().__init__(
            PimteController(self.drv),
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
