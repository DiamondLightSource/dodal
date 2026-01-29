from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.i10.i10_setting_data import I10Grating
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)
pgm_device = DeviceManager()


@pgm_device.factory()
def pgm() -> PlaneGratingMonochromator:
    "I10 Plane Grating Monochromator, it can change energy via pgm.energy.set(<energy>)"
    return PlaneGratingMonochromator(
        prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=I10Grating,
        grating_pv="NLINES2",
    )
