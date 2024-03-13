from typing import Sequence

from ophyd_async.core import DirectoryProvider, SignalR
from ophyd_async.epics.areadetector.writers import NDPluginBase

from dodal.devices.areadetector.pilatus import HDFStatsPilatus


class I22HDFStatsPilatus(HDFStatsPilatus):
    def __init__(
        self,
        prefix: str,
        directory_provider: DirectoryProvider,
        name: str,
        config_sigs: Sequence[SignalR] = (),
        **scalar_sigs: str,
    ):
        self.cdc = NDPluginBase(prefix + "CDC:")
        super().__init__(prefix, directory_provider, name, config_sigs, **scalar_sigs)
