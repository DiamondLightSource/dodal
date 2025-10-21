from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.i10 import I10JDiagnostic, I10JSlits, PiezoMirror
from dodal.devices.temperture_controller.lakeshore.lakeshore import Lakeshore336
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10-1")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix("i10", "J")


@device_factory()
def em_temperature_controller() -> Lakeshore336:
    return Lakeshore336(
        prefix=f"{PREFIX.beamline_prefix}-EA-TCTRL-41:",
    )


@device_factory()
def slits() -> I10JSlits:
    return I10JSlits(prefix=f"{PREFIX.beamline_prefix}-AL-SLITS-")


@device_factory()
def diagnostic() -> I10JDiagnostic:
    return I10JDiagnostic(
        prefix=f"{PREFIX.beamline_prefix}-DI-",
    )


@device_factory()
def focusing_mirror() -> PiezoMirror:
    return PiezoMirror(prefix=f"{PREFIX.beamline_prefix}-OP-FOCA-01:")
