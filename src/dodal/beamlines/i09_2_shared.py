from pathlib import Path

from daq_config_server.client import ConfigServer

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.i09.enums import Grating
from dodal.devices.i09_2_shared.i09_apple2 import (
    J09_GAP_POLY_DEG_COLUMNS,
    J09_PHASE_POLY_DEG_COLUMNS,
)
from dodal.devices.insertion_device import (
    Apple2,
    Apple2EnforceLHMoveController,
    BeamEnergy,
    InsertionDeviceEnergy,
    InsertionDevicePolarisation,
    UndulatorGap,
    UndulatorPhaseAxes,
)
from dodal.devices.insertion_device.energy_motor_lookup import (
    ConfigServerEnergyMotorLookup,
)
from dodal.devices.insertion_device.lookup_table_models import LookupTableColumnConfig
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

J09_CONF_CLIENT = ConfigServer(url="https://daq-config.diamond.ac.uk")
LOOK_UPTABLE_DIR = "/dls_sw/i09-2/software/gda/workspace_git/gda-diamond.git/configurations/i09-2-shared/lookupTables/"
GAP_LOOKUP_FILE_NAME = "JIDEnergy2GapCalibrations.csv"
PHASE_LOOKUP_FILE_NAME = "JIDEnergy2PhaseCalibrations.csv"

BL = get_beamline_name("i09-2-shared")
J_PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()


@devices.factory()
def pgm() -> PlaneGratingMonochromator:
    return PlaneGratingMonochromator(
        prefix=f"{J_PREFIX.beamline_prefix}-MO-PGM-01:",
        grating=Grating,
    )


@devices.factory()
def jid_gap() -> UndulatorGap:
    return UndulatorGap(prefix=f"{J_PREFIX.insertion_prefix}-MO-SERVC-01:")


@devices.factory()
def jid_phase() -> UndulatorPhaseAxes:
    return UndulatorPhaseAxes(
        prefix=f"{J_PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="PUO",
        top_inner="PUI",
        btm_inner="PLI",
        btm_outer="PLO",
    )


@devices.factory()
def jid(
    jid_gap: UndulatorGap, jid_phase: UndulatorPhaseAxes
) -> Apple2[UndulatorPhaseAxes]:
    """I09 soft x-ray insertion device."""
    return Apple2[UndulatorPhaseAxes](id_gap=jid_gap, id_phase=jid_phase)


@devices.factory()
def jid_controller(
    jid: Apple2[UndulatorPhaseAxes],
) -> Apple2EnforceLHMoveController[UndulatorPhaseAxes]:
    """J09 insertion device controller."""
    return Apple2EnforceLHMoveController[UndulatorPhaseAxes](
        apple2=jid,
        gap_energy_motor_lut=ConfigServerEnergyMotorLookup(
            lut_config=LookupTableColumnConfig(poly_deg=J09_GAP_POLY_DEG_COLUMNS),
            config_client=J09_CONF_CLIENT,
            path=Path(LOOK_UPTABLE_DIR, GAP_LOOKUP_FILE_NAME),
        ),
        phase_energy_motor_lut=ConfigServerEnergyMotorLookup(
            lut_config=LookupTableColumnConfig(poly_deg=J09_PHASE_POLY_DEG_COLUMNS),
            config_client=J09_CONF_CLIENT,
            path=Path(LOOK_UPTABLE_DIR, PHASE_LOOKUP_FILE_NAME),
        ),
        units="keV",
    )


@devices.factory()
def jid_energy(
    jid_controller: Apple2EnforceLHMoveController[UndulatorPhaseAxes],
) -> InsertionDeviceEnergy:
    return InsertionDeviceEnergy(id_controller=jid_controller)


@devices.factory()
def jid_polarisation(
    jid_controller: Apple2EnforceLHMoveController[UndulatorPhaseAxes],
) -> InsertionDevicePolarisation:
    return InsertionDevicePolarisation(id_controller=jid_controller)


@devices.factory()
def energy_jid(
    jid_energy: InsertionDeviceEnergy, pgm: PlaneGratingMonochromator
) -> BeamEnergy:
    """Beam energy."""
    return BeamEnergy(id_energy=jid_energy, mono=pgm.energy)
