from dodal.devices.i22.pilatus import I22HDFStatsPilatus
from ophyd_async.panda import PandA

from dodal.devices.linkam3 import Linkam3
from dodal.devices.tetramm import TetrammDetector
from dodal.parameters.gda_directory_provider import get_directory_provider


def saxs() -> I22HDFStatsPilatus:
    return I22HDFStatsPilatus(
        "BL22I-EA-PILAT-01",
        get_directory_provider(),
        name="saxs",
        temperature="Temperature",
    )


def waxs() -> I22HDFStatsPilatus:
    return I22HDFStatsPilatus(
        "BL22I-EA-PILAT-03", get_directory_provider(), name="waxs"
    )


def panda() -> PandA:
    panda = PandA("BL22I-EA-PANDA-01")
    panda.set_name("panda-01")
    return panda


def linkam() -> Linkam3:
    return Linkam3("BL22I-EA-TEMPC-05", name="linkam")


def tetramm1() -> TetrammDetector:
    return TetrammDetector("BL22I-EA-XBPM-02", get_directory_provider(), name="i0")


def tetramm2() -> TetrammDetector:
    return TetrammDetector("BL22I-EA-TTRM-02", get_directory_provider(), name="it")
