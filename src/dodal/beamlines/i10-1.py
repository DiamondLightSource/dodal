from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.temperture_controller.lakeshore.lakeshore import (
    LAKESHORE336_HEATER_SETTING,
    Lakeshore,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("I10-1")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def em_temperature_controller() -> Lakeshore:
    return Lakeshore(
        prefix=f"{PREFIX.beamline_prefix} +-EA-TCTRL-41:",
        num_readback_channel=4,
        heater_setting=LAKESHORE336_HEATER_SETTING,
    )
