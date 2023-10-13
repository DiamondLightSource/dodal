from typing import Sequence, Tuple, cast

from ophyd_async.core import DirectoryProvider, SignalR, StandardDetector
from ophyd_async.epics.areadetector.writers import HDFWriter, NDFileHDF, NDPluginStats
from ophyd_async.epics.areadetector.controllers import PilatusController
from ophyd_async.epics.areadetector.drivers import ADDriverShapeProvider, PilatusDriver


class HDFStatsPilatus(StandardDetector):
    _controller: PilatusController
    _writer: HDFWriter

    def __init__(
        self,
        prefix: str,
        directory_provider: DirectoryProvider,
        name: str = "",
        config_sigs: Sequence[Tuple[str, SignalR]] = (),
    ):
        self.drv = PilatusDriver(prefix + "DRV:")
        self.hdf = NDFileHDF(prefix + "HDF:")
        self.stats = NDPluginStats(prefix + "STATS:")

        self._config_sigs = list(config_sigs)
        super().__init__(
            PilatusController(self.drv),
            HDFWriter(
                self.hdf,
                directory_provider,
                lambda: self.name,
                ADDriverShapeProvider(self.drv),
                sum="NDStatsSum",
            ),
            name=name,
        )

    async def connect(self, sim: bool = False):
        await super().connect(sim=sim)
        driver = self._controller.driver
        self._config_sigs = [
            *self._config_sigs,
            *[
                (getattr(signal, "name"), cast(SignalR, signal))
                for signal in [driver.acquire_time, driver.acquire]
            ],
        ]
