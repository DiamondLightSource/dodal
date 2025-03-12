from dodal.common.beamlines.beamline_utils import device_factory
from dodal.devices.aithre_lasershaping.goniometer import Goniometer

PREFIX = "LA18L-MO-LSR-01:"


@device_factory()
def goniometer() -> Goniometer:
    return Goniometer(PREFIX, "aithre")
