from dodal.devices.areadetector import AdAravisDetector
from dodal.utils import BeamlinePrefix

PREFIX: str = BeamlinePrefix("p38").beamline_prefix


def d11(name: str = "D11") -> AdAravisDetector:
    return AdAravisDetector(name=name, prefix=f"{PREFIX}-DI-DCAM-03:")


def d12(name: str = "D12") -> AdAravisDetector:
    return AdAravisDetector(name=name, prefix=f"{PREFIX}-DI-DCAM-04:")
