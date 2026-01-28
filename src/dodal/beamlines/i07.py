from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.i07.dcm import DCM
from dodal.devices.i07.id import InsertionDevice
from dodal.devices.undulator import UndulatorOrder
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i07")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)

devices = DeviceManager()


@devices.factory()
def dcm() -> DCM:
    """Instantiate DCM using two PV bases"""
    return DCM(
        f"{PREFIX.beamline_prefix}-MO-DCM-01:", f"{PREFIX.beamline_prefix}-DI-DCM-01:"
    )


@devices.factory()
def harmonic() -> UndulatorOrder:
    return UndulatorOrder()


@devices.factory()
def id(harmonic: UndulatorOrder) -> InsertionDevice:
    """Get the i07 undulator device, instantiate it if it hasn't already been.
    If this is called when already instantiated it will return the existing object."""
    return InsertionDevice(
        f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        harmonic,
        id_gap_lookup_table_path="/dls_sw/i07/software/gda/config/lookupTables/IIDCalibrationTable.txt",
    )
