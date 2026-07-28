from dodal.beamlines.i06_shared import devices as i06_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i06_1 import DiffractionDichroism
from dodal.devices.beamlines.i06_1.magnet.temperature_controller import (
    SuperConductingMagnetTemperatureController,
)
from dodal.devices.motors import XYThetaStage
from dodal.devices.temperature_controller import Lakeshore336
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i06_1")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()
devices.include(i06_shared_devices)


@devices.factory()
def diff_cooling_temperature_controller() -> Lakeshore336:
    return Lakeshore336(prefix=f"{PREFIX.beamline_prefix}-EA-TCTRL-02:")


@devices.factory()
def diff_heating_temperature_controller() -> Lakeshore336:
    return Lakeshore336(prefix=f"{PREFIX.beamline_prefix}-EA-TCTRL-03:")


@devices.factory()
def xabs() -> XYThetaStage:
    return XYThetaStage(f"{PREFIX.beamline_prefix}-EA-XABS-01:")


@devices.factory()
def dd() -> DiffractionDichroism:
    return DiffractionDichroism(f"{PREFIX.beamline_prefix}-EA-DDIFF-01:")


@devices.factory()
def scm_temp_controller() -> SuperConductingMagnetTemperatureController:
    return SuperConductingMagnetTemperatureController(
        prefix=f"{PREFIX.beamline_prefix}-EA-TCTRL-01:"
    )
