from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.temperture_controller import (
    LAKESHORE340_PID_INPUT_CHANNEL,
    Lakeshore340,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i16")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)


@device_factory()
def temperature_controller() -> Lakeshore340:
    """Lakeshore 340 temperature controller"""
    return Lakeshore340(
        prefix=f"{PREFIX.beamline_prefix}-EA-LS340-01:",
        no_channels=4,
        heater_setting=int,
        pid_mode=int,
        input_channel_type=LAKESHORE340_PID_INPUT_CHANNEL,
    )
