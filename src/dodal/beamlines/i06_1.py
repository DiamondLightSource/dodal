from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.i06_1.ddiff import I06DDTemperatureController
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i06")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL, suffix="J")


@device_factory()
def temperature_controller() -> I06DDTemperatureController:
    """Lakeshore 336 controllers (DD)"""
    return I06DDTemperatureController(
        prefix=PREFIX.beamline_prefix,
    )
