from dodal.devices.areadetector.pilatus import HDFStatsPilatus
from ophyd_async.panda import PandA

from dodal.devices.linkam3 import Linkam3
from dodal.parameters.gda_directory_provider import get_directory_provider


def saxs() -> HDFStatsPilatus:
    return HDFStatsPilatus("BL22I-EA-PILAT-01:", get_directory_provider(), name="saxs")


def waxs() -> HDFStatsPilatus:
    return HDFStatsPilatus("BL22I-EA-PILAT-03:", get_directory_provider(), name="waxs")


def panda() -> PandA:
    panda = PandA("BL22I-EA-PANDA-01")
    panda.set_name("panda-01")
    return panda


#def linkam() -> Linkam3:
#    return Linkam3("BL22I-EA-TEMPC-01:", name="linkam")
