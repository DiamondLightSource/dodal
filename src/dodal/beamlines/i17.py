"""The I17 hardware doesn't exist yet, but this configuration file is useful for
creating plans in sm-bluesky as devices build up.
"""

from ophyd_async.core import StrictEnum

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i17.i17_apple2 import I17Apple2Controller
from dodal.devices.insertion_device import (
    Apple2,
    Apple2Controller,
    BeamEnergy,
    InsertionDeviceEnergy,
    InsertionDevicePolarisation,
    UndulatorGap,
    UndulatorPhaseAxes,
)
from dodal.devices.insertion_device.energy_motor_lookup import EnergyMotorLookup
from dodal.devices.insertion_device.lookup_table_models import LookupTable
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i17")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()


class I17Grating(StrictEnum):
    AU_400 = "400 line/mm Au"
    SI_400 = "400 line/mm Si"


@devices.factory
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory(skip=True)
def pgm() -> PlaneGratingMonochromator:
    return PlaneGratingMonochromator(
        prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=I17Grating,
        grating_pv="NLINES2",
    )


@devices.factory(skip=True)
def id_gap() -> UndulatorGap:
    return UndulatorGap(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


@devices.factory(skip=True)
def id_phase() -> UndulatorPhaseAxes:
    return UndulatorPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="RPQ1",
        top_inner="RPQ2",
        btm_inner="RPQ3",
        btm_outer="RPQ4",
    )


@devices.factory(skip=True)
def id(
    id_gap: UndulatorGap, id_phase: UndulatorPhaseAxes
) -> Apple2[UndulatorPhaseAxes]:
    return Apple2[UndulatorPhaseAxes](
        id_gap=id_gap,
        id_phase=id_phase,
    )


@devices.factory(skip=True)
def id_controller(
    id: Apple2[UndulatorPhaseAxes],
) -> Apple2Controller[Apple2[UndulatorPhaseAxes]]:
    """I17 insertion device controller with dummy energy to motor_converter."""
    return I17Apple2Controller(
        apple2=id,
        gap_energy_motor_lut=EnergyMotorLookup(lut=LookupTable()),
        phase_energy_motor_lut=EnergyMotorLookup(lut=LookupTable()),
    )


@devices.factory(skip=True)
def id_energy(
    id_controller: Apple2Controller[Apple2[UndulatorPhaseAxes]],
) -> InsertionDeviceEnergy:
    return InsertionDeviceEnergy(id_controller=id_controller)


@devices.factory(skip=True)
def id_polarisation(
    id_controller: Apple2Controller[Apple2[UndulatorPhaseAxes]],
) -> InsertionDevicePolarisation:
    return InsertionDevicePolarisation(id_controller=id_controller)


@devices.factory(skip=True)
def energy(
    id_energy: InsertionDeviceEnergy, pgm: PlaneGratingMonochromator
) -> BeamEnergy:
    return BeamEnergy(id_energy=id_energy, mono=pgm.energy)
