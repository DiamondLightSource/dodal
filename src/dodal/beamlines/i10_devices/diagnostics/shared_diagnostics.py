from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.i10 import (
    I10SharedDiagnostic,
    I10SharedSlitsDrainCurrent,
)

# Imports taken from i10 while we work out how to deal with split end stations
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)
devices_shared_diagnostics = DeviceManager()


@devices_shared_diagnostics.factory()
def optics_diagnostics() -> I10SharedDiagnostic:
    return I10SharedDiagnostic(
        prefix=f"{PREFIX.beamline_prefix}-DI-",
    )


@devices_shared_diagnostics.factory()
def optics_slits_current() -> I10SharedSlitsDrainCurrent:
    return I10SharedSlitsDrainCurrent(prefix=f"{PREFIX.beamline_prefix}-")
