"""The I17 hardware doesn't exist yet, but this configuration file is useful for
creating plans in sm-bluesky as devices build up."""

from ophyd_async.core import StrictEnum

from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.i17.i17_apple2 import I17Apple2Controller
from dodal.devices.insertion_device.apple2_undulator import (
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


class I17Grating(StrictEnum):
    AU_400 = "400 line/mm Au"
    SI_400 = "400 line/mm Si"


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory(skip=True)
def pgm() -> PlaneGratingMonochromator:
    return PlaneGratingMonochromator(
        prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=I17Grating,
        grating_pv="NLINES2",
    )


@device_factory()
def id_gap() -> UndulatorGap:
    return UndulatorGap(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


@device_factory()
def id_phase() -> UndulatorPhaseAxes:
    return UndulatorPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="RPQ1",
        top_inner="RPQ2",
        btm_inner="RPQ3",
        btm_outer="RPQ4",
    )


@device_factory(skip=True)
def id() -> Apple2:
    """I17 insertion device:"""
    return Apple2(
        id_gap=id_gap(),
        id_phase=id_phase(),
    )


@device_factory(skip=True)
def id_controller() -> Apple2Controller:
    """I17 insertion device controller with dummy energy to motor_converter."""
    return I17Apple2Controller(
        apple2=id(),
        gap_energy_motor_lut=EnergyMotorLookup(lut=LookupTable()),
        phase_energy_motor_lut=EnergyMotorLookup(lut=LookupTable()),
    )


@device_factory(skip=True)
def id_energy() -> InsertionDeviceEnergy:
    return InsertionDeviceEnergy(id_controller=id_controller())


@device_factory(skip=True)
def id_polarisation() -> InsertionDevicePolarisation:
    return InsertionDevicePolarisation(id_controller=id_controller())


@device_factory(skip=True)
def energy() -> BeamEnergy:
    """Beam energy."""
    return BeamEnergy(id_energy=id_energy(), mono=pgm().energy)
