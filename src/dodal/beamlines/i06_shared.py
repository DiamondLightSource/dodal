from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i06_shared import I06EpicsPolynomialDevice, I06Grating
from dodal.devices.beamlines.i06_shared.i06_apple2_controller import I06Apple2Controller
from dodal.devices.insertion_device import (
    Apple2,
    InsertionDevicePolarisation,
    UndulatorGap,
    UndulatorLockedPhaseAxes,
)
from dodal.devices.insertion_device.energy import InsertionDeviceEnergy
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i06")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def pgm() -> PlaneGratingMonochromator:
    return PlaneGratingMonochromator(
        prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=I06Grating,
        grating_pv="NLINES2",
    )


# Insertion Device
# ------------- Downstream Insertion Device --------------------
@devices.factory()
def i06_idd_epics_polynomial_device() -> I06EpicsPolynomialDevice:
    return I06EpicsPolynomialDevice(prefix=f"{PREFIX.beamline_prefix}-OP-IDD-01:")


@devices.factory()
def idd_gap() -> UndulatorGap:
    return UndulatorGap(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


@devices.factory()
def idd_phase() -> UndulatorLockedPhaseAxes:
    return UndulatorLockedPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="PL",
        btm_inner="PU",
    )


@devices.factory()
def idd(idd_gap: UndulatorGap, idd_phase: UndulatorLockedPhaseAxes) -> Apple2:
    """i06 downstream insertion device."""
    return Apple2(id_gap=idd_gap, id_phase=idd_phase)


@devices.factory()
def idd_controller(
    idd: Apple2, i06_idd_epics_polynomial_device: I06EpicsPolynomialDevice
) -> I06Apple2Controller:
    """I06 downstream insertion device controller."""
    return I06Apple2Controller(
        apple2=idd,
        gap_energy_motor_lut=i06_idd_epics_polynomial_device.energy_motor_lookup,
        phase_energy_motor_lut=i06_idd_epics_polynomial_device.energy_motor_lookup,  # need fix this too
        gap_motor_energy_lut=i06_idd_epics_polynomial_device.motor_energy_lookup,
    )


# -------------------- Upstream Insertion Device -------------------
@devices.factory()
def i06_idu_epics_polynomial_device() -> I06EpicsPolynomialDevice:
    return I06EpicsPolynomialDevice(prefix=f"{PREFIX.beamline_prefix}-OP-IDU-01:")


@devices.factory()
def idu_gap() -> UndulatorGap:
    return UndulatorGap(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-21:")


@devices.factory()
def idu_phase() -> UndulatorLockedPhaseAxes:
    return UndulatorLockedPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-21:",
        top_outer="PL",
        btm_inner="PU",
    )


@devices.factory()
def idu(idu_gap: UndulatorGap, idu_phase: UndulatorLockedPhaseAxes) -> Apple2:
    """i06 upstream insertion device."""
    return Apple2(id_gap=idu_gap, id_phase=idu_phase)


@devices.factory()
def idu_controller(
    idu: Apple2, i06_idu_epics_polynomial_device: I06EpicsPolynomialDevice
) -> I06Apple2Controller:
    """I06 upstream insertion device controller."""
    return I06Apple2Controller(
        apple2=idu,
        gap_energy_motor_lut=i06_idu_epics_polynomial_device.energy_motor_lookup,
        phase_energy_motor_lut=i06_idu_epics_polynomial_device.energy_motor_lookup,  # need fix this too
        gap_motor_energy_lut=i06_idu_epics_polynomial_device.motor_energy_lookup,
    )


@devices.factory()
def idu_energy(idu_controller: I06Apple2Controller) -> InsertionDeviceEnergy:
    return InsertionDeviceEnergy(id_controller=idu_controller)


@devices.factory()
def idu_polarisation(
    idu_controller: I06Apple2Controller,
) -> InsertionDevicePolarisation:
    return InsertionDevicePolarisation(id_controller=idu_controller)
