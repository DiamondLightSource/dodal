from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.temperture_controller import Lakeshore336, Lakeshore340
from dodal.devices.undulator import UndulatorInMm, UndulatorOrder
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i16")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)


devices = DeviceManager()


@devices.factory()
def id() -> UndulatorInMm:
    return UndulatorInMm(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


@devices.factory()
def harmonic() -> UndulatorOrder:
    return UndulatorOrder()


@devices.factory()
def lakeshore340() -> Lakeshore340:
    return Lakeshore340(prefix=f"{PREFIX.beamline_prefix}-EA-LS340-01:")


@devices.factory()
def lakeshore336() -> Lakeshore336:
    return Lakeshore336(prefix=f"{PREFIX.beamline_prefix}-EA-LS336-01:")
