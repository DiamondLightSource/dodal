from dodal.devices.areadetector import SumHDFAravisDetector
from dodal.utils import BeamlinePrefix
from dodal.parameters.gda_directory_provider import get_directory_provider

PREFIX: str = BeamlinePrefix("p38").beamline_prefix


def d11() -> SumHDFAravisDetector:
    return SumHDFAravisDetector(
        f"{PREFIX}-DI-DCAM-03:",
        directory_provider=get_directory_provider(),
    )


def d12() -> SumHDFAravisDetector:
    return SumHDFAravisDetector(
        f"{PREFIX}-DI-DCAM-04:",
        directory_provider=get_directory_provider(),
    )
