from dodal.common.beamlines.beamline_utils import device_factory
from dodal.devices.aithre_lasershaping.goniometer import AithreGoniometer

PREFIX = "LA18L"


@device_factory()
def goniometer() -> AithreGoniometer:
    return AithreGoniometer(f"{PREFIX}-MO-LSR-01:", "goniometer")
