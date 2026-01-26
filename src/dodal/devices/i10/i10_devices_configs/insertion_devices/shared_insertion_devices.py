"""
note:
    I10 has two insertion devices one up(idu) and one down stream(idd).
    It is worth noting that the downstream device is slightly longer,
    so it can reach Mn edge for linear arbitrary.
    idd == id1,    idu == id2.
"""

from pathlib import Path

from daq_config_server.client import ConfigServer

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.i10.i10_apple2 import (
    I10Apple2,
    I10Apple2Controller,
    LinearArbitraryAngle,
)

# Imports taken from i10 while we work out how to deal with split end stations
from dodal.devices.insertion_device import (
    BeamEnergy,
    InsertionDeviceEnergy,
    InsertionDevicePolarisation,
    UndulatorGap,
    UndulatorJawPhase,
    UndulatorPhaseAxes,
)
from dodal.devices.insertion_device.energy_motor_lookup import (
    ConfigServerEnergyMotorLookup,
)
from dodal.devices.insertion_device.lookup_table_models import (
    DEFAULT_GAP_FILE,
    DEFAULT_PHASE_FILE,
    LookupTableColumnConfig,
    Source,
)
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i10")
set_log_beamline(BL)
set_utils_beamline(BL)
PREFIX = BeamlinePrefix(BL)
devices_idd = DeviceManager()

devices_idu = DeviceManager()

"""ID"""

I10_CONF_CLIENT = ConfigServer(url="https://daq-config.diamond.ac.uk")

LOOK_UPTABLE_DIR = "/dls_sw/i10/software/gda/workspace_git/gda-diamond.git/configurations/i10-shared/lookupTables/"


@devices_idd.factory()
def idd_gap() -> UndulatorGap:
    return UndulatorGap(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


@devices_idd.factory()
def idd_phase() -> UndulatorPhaseAxes:
    return UndulatorPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="RPQ1",
        top_inner="RPQ2",
        btm_inner="RPQ3",
        btm_outer="RPQ4",
    )


@devices_idd.factory()
def idd_jaw_phase() -> UndulatorJawPhase:
    return UndulatorJawPhase(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        move_pv="RPQ1",
    )


@devices_idd.factory()
def idd(
    idd_gap: UndulatorGap,
    idd_phase: UndulatorPhaseAxes,
    idd_jaw_phase: UndulatorJawPhase,
) -> I10Apple2:
    """i10 downstream insertion device:"""
    return I10Apple2(id_gap=idd_gap, id_phase=idd_phase, id_jaw_phase=idd_jaw_phase)


@devices_idd.factory()
def idd_controller(idd: I10Apple2) -> I10Apple2Controller:
    """I10 downstream insertion device controller."""
    source = Source(column="Source", value="idd")
    idd_gap_energy_motor_lut = ConfigServerEnergyMotorLookup(
        config_client=I10_CONF_CLIENT,
        lut_config=LookupTableColumnConfig(source=source),
        path=Path(LOOK_UPTABLE_DIR, DEFAULT_GAP_FILE),
    )
    idd_phase_energy_motor_lut = ConfigServerEnergyMotorLookup(
        config_client=I10_CONF_CLIENT,
        lut_config=LookupTableColumnConfig(source=source),
        path=Path(LOOK_UPTABLE_DIR, DEFAULT_PHASE_FILE),
    )
    return I10Apple2Controller(
        apple2=idd,
        gap_energy_motor_lut=idd_gap_energy_motor_lut,
        phase_energy_motor_lut=idd_phase_energy_motor_lut,
    )


@devices_idd.factory()
def idd_energy(idd_controller: I10Apple2Controller) -> InsertionDeviceEnergy:
    return InsertionDeviceEnergy(id_controller=idd_controller)


@devices_idd.factory()
def idd_polarisation(
    idd_controller: I10Apple2Controller,
) -> InsertionDevicePolarisation:
    return InsertionDevicePolarisation(id_controller=idd_controller)


@devices_idd.factory()
def idd_laa(idd_controller: I10Apple2Controller) -> LinearArbitraryAngle:
    return LinearArbitraryAngle(id_controller=idd_controller)


@devices_idd.factory()
def energy_dd(
    idd_energy: InsertionDeviceEnergy, pgm: PlaneGratingMonochromator
) -> BeamEnergy:
    """Beam energy from down energy devices."""
    return BeamEnergy(id_energy=idd_energy, mono=pgm.energy)


@devices_idu.factory()
def idu_gap() -> UndulatorGap:
    return UndulatorGap(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-21:")


@devices_idu.factory()
def idu_phase() -> UndulatorPhaseAxes:
    return UndulatorPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-21:",
        top_outer="RPQ1",
        top_inner="RPQ2",
        btm_inner="RPQ3",
        btm_outer="RPQ4",
    )


@devices_idu.factory()
def idu_jaw_phase() -> UndulatorJawPhase:
    return UndulatorJawPhase(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-21:",
        move_pv="RPQ1",
    )


@devices_idu.factory()
def idu(
    idu_gap: UndulatorGap,
    idu_phase: UndulatorPhaseAxes,
    idu_jaw_phase: UndulatorJawPhase,
) -> I10Apple2:
    """i10 upstream insertion device"""
    return I10Apple2(id_gap=idu_gap, id_phase=idu_phase, id_jaw_phase=idu_jaw_phase)


@devices_idu.factory()
def idu_controller(idu: I10Apple2) -> I10Apple2Controller:
    """I10 upstream insertion device controller."""
    source = Source(column="Source", value="idu")
    idu_gap_energy_motor_lut = ConfigServerEnergyMotorLookup(
        config_client=I10_CONF_CLIENT,
        lut_config=LookupTableColumnConfig(source=source),
        path=Path(LOOK_UPTABLE_DIR, DEFAULT_GAP_FILE),
    )
    idu_phase_energy_motor_lut = ConfigServerEnergyMotorLookup(
        config_client=I10_CONF_CLIENT,
        lut_config=LookupTableColumnConfig(source=source),
        path=Path(LOOK_UPTABLE_DIR, DEFAULT_PHASE_FILE),
    )
    return I10Apple2Controller(
        apple2=idu,
        gap_energy_motor_lut=idu_gap_energy_motor_lut,
        phase_energy_motor_lut=idu_phase_energy_motor_lut,
    )


@devices_idu.factory()
def idu_energy(idu_controller: I10Apple2Controller) -> InsertionDeviceEnergy:
    return InsertionDeviceEnergy(id_controller=idu_controller)


@devices_idu.factory()
def idu_polarisation(
    idu_controller: I10Apple2Controller,
) -> InsertionDevicePolarisation:
    return InsertionDevicePolarisation(id_controller=idu_controller)


@devices_idu.factory()
def idu_laa(idu_controller: I10Apple2Controller) -> LinearArbitraryAngle:
    return LinearArbitraryAngle(id_controller=idu_controller)


@devices_idu.factory()
def energy_ud(
    idu_energy: InsertionDeviceEnergy, pgm: PlaneGratingMonochromator
) -> BeamEnergy:
    """Beam energy from down energy devices."""
    return BeamEnergy(id_energy=idu_energy, mono=pgm.energy)
