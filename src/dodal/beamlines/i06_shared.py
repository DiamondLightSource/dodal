from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i06_shared import I06EpicsPolynomialDevice, I06Grating
from dodal.devices.beamlines.i06_shared.i06_apple2_controller import I06Apple2Controller
from dodal.devices.insertion_device import (
    Apple2,
    InsertionDeviceEnergy,
    InsertionDevicePolarisation,
    UndulatorAccessControl,
    UndulatorGap,
    UndulatorLockedPhaseAxes,
)
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


@devices.factory()
def idd_polynomial() -> I06EpicsPolynomialDevice:
    return I06EpicsPolynomialDevice(prefix=f"{PREFIX.beamline_prefix}-OP-IDD-01:")


@devices.factory()
def idd_accesscontrol() -> UndulatorAccessControl:
    return UndulatorAccessControl(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


@devices.factory()
def idd_gap(idd_accesscontrol: UndulatorAccessControl) -> UndulatorGap:
    return UndulatorGap(f"{PREFIX.insertion_prefix}-MO-SERVC-01:", idd_accesscontrol)


@devices.factory()
def idd_phase(idd_accesscontrol: UndulatorAccessControl) -> UndulatorLockedPhaseAxes:
    return UndulatorLockedPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="PL",
        btm_inner="PU",
        access_control=idd_accesscontrol,
    )


@devices.factory()
def idd(
    idd_gap: UndulatorGap,
    idd_phase: UndulatorLockedPhaseAxes,
    idd_accesscontrol: UndulatorAccessControl,
) -> Apple2:
    """i06 downstream insertion device."""
    return Apple2(gap=idd_gap, phase=idd_phase, access_control=idd_accesscontrol)


@devices.factory()
def idd_controller(
    idd: Apple2, idd_polynomial: I06EpicsPolynomialDevice
) -> I06Apple2Controller:
    """I06 downstream insertion device controller."""
    return I06Apple2Controller(
        apple2=idd,
        gap_energy_motor_lut=idd_polynomial.energy_gap_motor_lookup,
        phase_energy_motor_lut=idd_polynomial.energy_phase_motor_lookup,
        inverse_gap_energy_motor_lut=idd_polynomial.gap_motor_energy_lookup,
    )


@devices.factory()
def idu_polynomial() -> I06EpicsPolynomialDevice:
    return I06EpicsPolynomialDevice(prefix=f"{PREFIX.beamline_prefix}-OP-IDU-01:")


@devices.factory()
def idu_accesscontrol() -> UndulatorAccessControl:
    return UndulatorAccessControl(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-21:")


@devices.factory()
def idu_gap(idu_accesscontrol: UndulatorAccessControl) -> UndulatorGap:
    return UndulatorGap(f"{PREFIX.insertion_prefix}-MO-SERVC-21:", idu_accesscontrol)


@devices.factory()
def idu_phase(idu_accesscontrol: UndulatorAccessControl) -> UndulatorLockedPhaseAxes:
    return UndulatorLockedPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-21:",
        top_outer="PL",
        btm_inner="PU",
        access_control=idu_accesscontrol,
    )


@devices.factory()
def idu(
    idu_gap: UndulatorGap,
    idu_phase: UndulatorLockedPhaseAxes,
    idu_accesscontrol: UndulatorAccessControl,
) -> Apple2:
    """i06 upstream insertion device."""
    return Apple2(gap=idu_gap, phase=idu_phase, access_control=idu_accesscontrol)


@devices.factory()
def idu_controller(
    idu: Apple2, idu_polynomial: I06EpicsPolynomialDevice
) -> I06Apple2Controller:
    """I06 upstream insertion device controller."""
    return I06Apple2Controller(
        apple2=idu,
        gap_energy_motor_lut=idu_polynomial.energy_gap_motor_lookup,
        phase_energy_motor_lut=idu_polynomial.energy_phase_motor_lookup,
        inverse_gap_energy_motor_lut=idu_polynomial.gap_motor_energy_lookup,
    )


@devices.factory()
def idu_energy(idu_controller: I06Apple2Controller) -> InsertionDeviceEnergy:
    return InsertionDeviceEnergy(id_controller=idu_controller)


@devices.factory()
def idu_polarisation(
    idu_controller: I06Apple2Controller,
) -> InsertionDevicePolarisation:
    return InsertionDevicePolarisation(id_controller=idu_controller)
