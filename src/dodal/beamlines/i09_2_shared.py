from pathlib import Path

from daq_config_server.client import ConfigClient

from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i09.enums import Grating
from dodal.devices.beamlines.i09_2_shared.i09_apple2 import (
    J09_GAP_POLY_DEG_COLUMNS,
    J09_PHASE_POLY_DEG_COLUMNS,
)
from dodal.devices.hutch_shutter import HutchShutter
from dodal.devices.insertion_device import (
    Apple2,
    Apple2EnforceLHMoveController,
    BeamEnergy,
    InsertionDeviceEnergy,
    InsertionDevicePolarisation,
    LookupTableColumnConfig,
)
from dodal.devices.insertion_device.energy_motor_lookup import (
    ConfigServerEnergyMotorLookup,
)
from dodal.devices.insertion_device.undulator import (
    UndulatorAccessControl,
    UndulatorGap,
    UndulatorPhaseAxes,
)
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.utils import BeamlinePrefix, get_beamline_name

LOOK_UPTABLE_DIR = "/dls_sw/i09-2/software/gda/workspace_git/gda-diamond.git/configurations/i09-2-shared/lookupTables/"
GAP_LOOKUP_FILE_NAME = "JIDEnergy2GapCalibrations.csv"
PHASE_LOOKUP_FILE_NAME = "JIDEnergy2PhaseCalibrations.csv"

BL = get_beamline_name("i09-2-shared")
J_PREFIX = BeamlinePrefix(BL, suffix="J")
K_PREFIX = BeamlinePrefix(BL, suffix="K")

devices = DeviceManager()


@devices.fixture
def config_client() -> ConfigClient:
    return ConfigClient.from_url()


@devices.factory()
def psk1() -> HutchShutter:
    return HutchShutter(K_PREFIX.beamline_prefix)


@devices.factory()
def pgm() -> PlaneGratingMonochromator:
    return PlaneGratingMonochromator(
        prefix=f"{J_PREFIX.beamline_prefix}-MO-PGM-01:",
        grating=Grating,
    )


@devices.factory()
def jid_accesscontrol() -> UndulatorAccessControl:
    return UndulatorAccessControl(prefix=f"{J_PREFIX.insertion_prefix}-MO-SERVC-01:")


@devices.factory()
def jgap(jid_accesscontrol: UndulatorAccessControl) -> UndulatorGap:
    return UndulatorGap(f"{J_PREFIX.insertion_prefix}-MO-SERVC-01:", jid_accesscontrol)


@devices.factory()
def jphase(jid_accesscontrol: UndulatorAccessControl) -> UndulatorPhaseAxes:
    return UndulatorPhaseAxes(
        prefix=f"{J_PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="PUO",
        top_inner="PUI",
        btm_inner="PLI",
        btm_outer="PLO",
        access_control=jid_accesscontrol,
    )


@devices.factory()
def jid(
    jgap: UndulatorGap, jphase: UndulatorPhaseAxes, jid_accesscontrol
) -> Apple2[UndulatorPhaseAxes]:
    """I09 soft x-ray insertion device."""
    return Apple2[UndulatorPhaseAxes](
        gap=jgap, phase=jphase, access_control=jid_accesscontrol
    )


@devices.factory()
def jidcontroller(
    jid: Apple2[UndulatorPhaseAxes],
    config_client: ConfigClient,
) -> Apple2EnforceLHMoveController[UndulatorPhaseAxes]:
    """J09 insertion device controller."""
    return Apple2EnforceLHMoveController[UndulatorPhaseAxes](
        apple2=jid,
        gap_energy_motor_lut=ConfigServerEnergyMotorLookup(
            lut_config=LookupTableColumnConfig(poly_deg=J09_GAP_POLY_DEG_COLUMNS),
            config_client=config_client,
            path=Path(LOOK_UPTABLE_DIR, GAP_LOOKUP_FILE_NAME),
        ),
        phase_energy_motor_lut=ConfigServerEnergyMotorLookup(
            lut_config=LookupTableColumnConfig(poly_deg=J09_PHASE_POLY_DEG_COLUMNS),
            config_client=config_client,
            path=Path(LOOK_UPTABLE_DIR, PHASE_LOOKUP_FILE_NAME),
        ),
        units="keV",
    )


@devices.factory()
def jidenergy(
    jidcontroller: Apple2EnforceLHMoveController[UndulatorPhaseAxes],
) -> InsertionDeviceEnergy:
    return InsertionDeviceEnergy(id_controller=jidcontroller)


@devices.factory()
def jpolarisation(
    jidcontroller: Apple2EnforceLHMoveController[UndulatorPhaseAxes],
) -> InsertionDevicePolarisation:
    return InsertionDevicePolarisation(id_controller=jidcontroller)


@devices.factory()
def jenergy(
    jidenergy: InsertionDeviceEnergy, pgm: PlaneGratingMonochromator
) -> BeamEnergy:
    """Beam energy."""
    return BeamEnergy(id_energy=jidenergy, mono=pgm.energy)
