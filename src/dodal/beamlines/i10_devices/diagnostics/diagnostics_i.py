from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.i10 import (
    I10Diagnostic,
    I10Diagnostic5ADet,
)
from dodal.devices.i10.diagnostics import I10Diagnostic, I10Diagnostic5ADet

# Imports taken from i10 while we work out how to deal with split end stations
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)
devices_diagnostics_i = DeviceManager()


@devices_diagnostics_i.factory()
def diagnostics() -> I10Diagnostic:
    return I10Diagnostic(
        prefix=f"{PREFIX.beamline_prefix}-DI-",
    )


@devices_diagnostics_i.factory()
def d5a_det() -> I10Diagnostic5ADet:
    return I10Diagnostic5ADet(prefix=f"{PREFIX.beamline_prefix}-DI-")
