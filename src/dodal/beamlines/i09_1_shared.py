from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.devices.i09.dcm import DCM
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i09-1")
PREFIX = BeamlinePrefix(BL, suffix="I")


@device_factory()
def dcm() -> DCM:
    return DCM(prefix=f"{PREFIX.beamline_prefix}-MO-DCM-01:")
