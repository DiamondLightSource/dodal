from dodal.devices.areadetector.adaravis import SumHDFAravisDetector
from dodal.parameters.gda_directory_provider import get_directory_provider
from dodal.utils import BeamlinePrefix

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
