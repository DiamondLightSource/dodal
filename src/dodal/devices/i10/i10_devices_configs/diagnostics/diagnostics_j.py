from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.i10.diagnostics import (
    I10JDiagnostic,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10-1")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix("i10", "J")
devices_diagnostics_j = DeviceManager()


@devices_diagnostics_j.factory()
def diagnostic() -> I10JDiagnostic:
    return I10JDiagnostic(
        prefix=f"{PREFIX.beamline_prefix}-DI-",
    )
