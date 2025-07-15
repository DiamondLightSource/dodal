from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.temperture_controller.lakeshore_controller import (
    Lakeshore,
    Lakeshore336,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i21")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)


@device_factory()
def temperature_controller() -> Lakeshore:
    """Lakeshore temperature controller, it can control temperature via
    temperature_controller.temperature.set(<temperature>).
    """
    return Lakeshore(
        f"{PREFIX.beamline_prefix}-EA-TCTRL-01:",
        no_channels=4,
        heater_table=Lakeshore336,
    )
