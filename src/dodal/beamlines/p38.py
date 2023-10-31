from dodal.devices.areadetector.adaravis import SumHDFAravisDetector
from dodal.parameters.gda_directory_provider import get_directory_provider
from dodal.utils import BeamlinePrefix
from dodal.devices.linkam3 import Linkam3
from dodal.devices.tetramm import TetrammDetector

from ophyd_async.panda import PandA

PREFIX: str = BeamlinePrefix("p38").beamline_prefix


def d11() -> SumHDFAravisDetector:
    return SumHDFAravisDetector(
        f"{PREFIX}-DI-DCAM-03",
        directory_provider=get_directory_provider(),
        name="d11",
    )


def d12() -> SumHDFAravisDetector:
    return SumHDFAravisDetector(
        f"{PREFIX}-DI-DCAM-04",
        directory_provider=get_directory_provider(),
        name="d12",
    )


def linkam3() -> Linkam3:
    return Linkam3(f"{PREFIX}-EA-LINKM-02", name="linkam3")


def tetramm() -> TetrammDetector:
    return TetrammDetector(f"{PREFIX}-EA-XBPM-01", directory_provider=get_directory_provider(), name="tetramm")


def panda() -> PandA:
    panda = PandA("BL38P-EA-PANDA-01")
    panda.set_name("panda") 
    return panda

