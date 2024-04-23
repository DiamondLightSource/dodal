from ophyd_async.core import DirectoryProvider
from ophyd_async.epics.areadetector import AravisDetector
from ophyd_async.epics.areadetector.drivers import AravisDriver
from ophyd_async.epics.areadetector.writers import NDFileHDF


def DLSAravis(
    prefix: str, name: str, directory_provider: DirectoryProvider
) -> AravisDetector:
    return AravisDetector(
        name=name,
        directory_provider=directory_provider,
        driver=AravisDriver(prefix + "DET:"),
        hdf=NDFileHDF(prefix + "HDF5:"),
    )
