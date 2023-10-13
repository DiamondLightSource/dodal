from ophyd_async.core import DirectoryProvider
from ophyd_async.epics.areadetector import HDFStatsPilatus
from ophyd_async.panda import PandA

from ..devices.linkam import Linkam


def saxs(directory_provider: DirectoryProvider) -> HDFStatsPilatus:
    return HDFStatsPilatus("BL22I-EA-DET-01:", directory_provider)


def waxs(directory_provider: DirectoryProvider) -> HDFStatsPilatus:
    return HDFStatsPilatus("BL22I-EA-DET-02:", directory_provider)


def panda(**kwargs) -> PandA:
    return PandA("BL22I-MO-PANDA-01:")


def linkam(**kwargs) -> Linkam:
    return Linkam("BL22I-EA-TEMPC-01:")
