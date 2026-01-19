from pathlib import Path

from daq_config_server.client import ConfigServer

from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.i21 import (
    Grating,
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
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.temperture_controller import (
    Lakeshore336,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i21")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)

I21_PHASE_POLY_DEG_COLUMNS = ["b"]
I21_GRATING_COLUMNS = "Grating"

I21_CONF_CLIENT = ConfigServer(url="https://daq-config.diamond.ac.uk")
LOOK_UPTABLE_DIR = "/dls_sw/i21/software/gda/workspace_git/gda-diamond.git/configurations/i21-config/lookupTables/"
GAP_LOOKUP_FILE_NAME = "IDEnergy2GapCalibrations.csv"
PHASE_LOOKUP_FILE_NAME = "IDEnergy2PhaseCalibrations.csv"


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def pgm() -> PlaneGratingMonochromator:
    return PlaneGratingMonochromator(
        prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=Grating,
    )


@device_factory()
def id_gap() -> UndulatorGap:
    return UndulatorGap(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


@device_factory()
def id_phase() -> UndulatorPhaseAxes:
    return UndulatorPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="PUO",
        top_inner="PUI",
        btm_inner="PLI",
        btm_outer="PLO",
    )


@device_factory()
def id() -> Apple2[UndulatorPhaseAxes]:
    """I21 insertion device."""
    return Apple2[UndulatorPhaseAxes](
        id_gap=id_gap(),
        id_phase=id_phase(),
    )


@device_factory()
def id_controller() -> Apple2EnforceLHMoveController[UndulatorPhaseAxes]:
    """i21 insertion device controller."""
    return Apple2EnforceLHMoveController[UndulatorPhaseAxes](
        apple2=id(),
        gap_energy_motor_lut=ConfigServerEnergyMotorLookup(
            lut_config=LookupTableColumnConfig(grating=I21_GRATING_COLUMNS),
            config_client=I21_CONF_CLIENT,
            path=Path(LOOK_UPTABLE_DIR, GAP_LOOKUP_FILE_NAME),
        ),
        phase_energy_motor_lut=ConfigServerEnergyMotorLookup(
            lut_config=LookupTableColumnConfig(
                grating=I21_GRATING_COLUMNS, poly_deg=I21_PHASE_POLY_DEG_COLUMNS
            ),
            config_client=I21_CONF_CLIENT,
            path=Path(LOOK_UPTABLE_DIR, GAP_LOOKUP_FILE_NAME),
        ),
        units="eV",
    )


@device_factory()
def id_energy() -> InsertionDeviceEnergy:
    return InsertionDeviceEnergy(id_controller=id_controller())


@device_factory()
def id_polarisation() -> InsertionDevicePolarisation:
    return InsertionDevicePolarisation(id_controller=id_controller())


@device_factory()
def energy_jid() -> BeamEnergy:
    """Beam energy."""
    return BeamEnergy(id_energy=id_energy(), mono=pgm().energy)


@device_factory()
def sample_temperature_controller() -> Lakeshore336:
    return Lakeshore336(prefix=f"{PREFIX.beamline_prefix}-EA-TCTRL-01:")
