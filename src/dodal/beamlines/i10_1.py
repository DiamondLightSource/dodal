from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.temperture_controller import (
    LAKESHORE336_HEATER_SETTING,
    LAKESHORE336_PID_INPUT_CHANNEL,
    LAKESHORE336_PID_MODE,
    Lakeshore336,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10-1")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL, suffix="J")


@device_factory()
def temperature_controller() -> Lakeshore336:
    """Lakeshore temperature controller, it can control temperature via
    temperature_controller.temperature.set(<temperature>).
    """
    return Lakeshore336(
        prefix=f"{PREFIX.beamline_prefix}-EA-TCTRL-41:",
        no_channels=4,
        heater_setting=LAKESHORE336_HEATER_SETTING,
        pid_mode=LAKESHORE336_PID_MODE,
        input_channel_type=LAKESHORE336_PID_INPUT_CHANNEL,
    )
