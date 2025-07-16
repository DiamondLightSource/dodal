from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.temperture_controller import (
    LAKESHORE336,
    LAKESHORE336_PID_MODE,
    PID_INPUT_CHANNEL,
    Lakeshore,
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
        heater_setting=LAKESHORE336,
        pid_mode=LAKESHORE336_PID_MODE,
        input_signal_type=PID_INPUT_CHANNEL,
    )
