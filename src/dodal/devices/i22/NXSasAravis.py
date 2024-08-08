from ophyd_async.core import DirectoryProvider
from ophyd_async.epics.areadetector import AravisDetector

from dodal.devices.i22.nxsas import NXSasMetadataHolder


class NXSasAravis(AravisDetector):
    metadata_holder: NXSasMetadataHolder

    def __init__(
        self,
        prefix: str,
        directory_provider: DirectoryProvider,
        name: str,
        metadata_holder: NXSasMetadataHolder,
    ):
        self._metadata_holder = metadata_holder
        super().__init__(
            prefix=prefix,
            directory_provider=directory_provider,
            name=name,
        )
