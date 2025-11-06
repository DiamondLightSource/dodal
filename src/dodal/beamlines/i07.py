from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.i07.dcm import DCM
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i07")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)


@device_factory()
def dcm() -> DCM:
    """Instantiate DCM using two PV bases"""
    dcm = DCM(
        f"{PREFIX.beamline_prefix}-MO-DCM-01:",
        f"{PREFIX.beamline_prefix}-DI-DCM-01:",
        "dcm",
    )
    return dcm
