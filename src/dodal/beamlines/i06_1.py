from dodal.beamlines.i06_shared import devices as i06_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i06_1 import DiffractionDichroism
from dodal.devices.beamlines.i06_1.magnet import (
    MagnetThreeAxesRampRateController,
    SuperConductingMagnetController,
)
from dodal.devices.motors import XYThetaStage
from dodal.devices.temperture_controller import Lakeshore336
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i06_1")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()
devices.include(i06_shared_devices)


@devices.factory()
def ls336_cooling() -> Lakeshore336:
    return Lakeshore336(prefix=f"{PREFIX.beamline_prefix}-EA-TCTRL-02:")


@devices.factory()
def ls336_heating() -> Lakeshore336:
    return Lakeshore336(prefix=f"{PREFIX.beamline_prefix}-EA-TCTRL-03:")


@devices.factory()
def xabs() -> XYThetaStage:
    return XYThetaStage(f"{PREFIX.beamline_prefix}-EA-XABS-01:")


@devices.factory()
def dd() -> DiffractionDichroism:
    return DiffractionDichroism(f"{PREFIX.beamline_prefix}-EA-DDIFF-01:")


@devices.factory()
def mag_ramp_rate() -> MagnetThreeAxesRampRateController:
    return MagnetThreeAxesRampRateController(f"{PREFIX.beamline_prefix}-EA-SMC")


@devices.factory()
def scmc(
    mag_ramp_rate: MagnetThreeAxesRampRateController,
) -> SuperConductingMagnetController:
    return SuperConductingMagnetController(
        f"{PREFIX.beamline_prefix}-EA-MAG-01:", mag_ramp_rate
    )
