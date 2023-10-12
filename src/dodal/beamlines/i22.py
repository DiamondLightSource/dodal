from ..devices.linkam import Linkam
from ..parameters.gda_directory_provider import GDADirectoryProvider
from ophyd_async.epics.areadetector import HDFStatsPilatus
from ophyd_async.panda import PandA


def saxs(directory_provider: GDADirectoryProvider) -> HDFStatsPilatus:
    return HDFStatsPilatus("BL22I-EA-DET-01:", directory_provider)


def waxs(directory_provider: GDADirectoryProvider) -> HDFStatsPilatus:
    return HDFStatsPilatus("BL22I-EA-DET-02:", directory_provider)


def panda(**kwargs) -> PandA:
    return PandA("BL22I-MO-PANDA-01:")


def linkam(**kwargs) -> Linkam:
    return Linkam("BL22I-EA-TEMPC-01:")
