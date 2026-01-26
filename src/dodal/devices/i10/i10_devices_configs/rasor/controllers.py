from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.temperture_controller import (
    Lakeshore340,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)
devices_rasor_temperature_controller = DeviceManager()


@devices_rasor_temperature_controller.factory()
def rasor_temperature_controller() -> Lakeshore340:
    return Lakeshore340(
        prefix="ME01D-EA-TCTRL-01:",
    )
