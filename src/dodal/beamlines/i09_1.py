from dodal.beamlines.i09_1_shared import devices as i09_1_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.common_dcm import DoubleCrystalMonochromatorWithDSpacing
from dodal.devices.electron_analyser.base import EnergySource
from dodal.devices.i09_1 import SpecsPhoibos225
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.temperture_controller import Lakeshore336
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i09-1")
PREFIX = BeamlinePrefix(BL, suffix="I")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()
devices.include(i09_1_shared_devices)


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def energy_source(dcm: DoubleCrystalMonochromatorWithDSpacing) -> EnergySource:
    return EnergySource(dcm.energy_in_eV)


# CAM:IMAGE will fail to connect outside the beamline network,
# see https://github.com/DiamondLightSource/dodal/issues/1852
@devices.factory()
def analyser(energy_source: EnergySource) -> SpecsPhoibos225:
    return SpecsPhoibos225(f"{PREFIX.beamline_prefix}-EA-DET-02:CAM:", energy_source)


@devices.factory()
def lakeshore() -> Lakeshore336:
    return Lakeshore336(prefix=f"{PREFIX.beamline_prefix}-EA-TCTRL-01:")
