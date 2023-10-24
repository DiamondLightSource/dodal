from ophyd_async.epics.areadetector import HDFStatsPilatus
from ophyd_async.panda import PandA

from dodal.devices.linkam3 import Linkam3
from dodal.parameters.gda_directory_provider import get_directory_provider


def saxs() -> HDFStatsPilatus:
    return HDFStatsPilatus("BL22I-EA-DET-01:", get_directory_provider())


def waxs() -> HDFStatsPilatus:
    return HDFStatsPilatus("BL22I-EA-DET-02:", get_directory_provider())


def panda() -> PandA:
    return PandA("BL22I-MO-PANDA-01:")


def linkam() -> Linkam3:
    return Linkam3("BL22I-EA-TEMPC-01:", name="linkam")
