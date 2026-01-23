from pathlib import Path

from daq_config_server.client import ConfigServer
from ophyd_async.core import StrictEnum

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.insertion_device import (
    Apple2,
    Apple2EnforceLHMoveController,
    ConfigServerEnergyMotorLookup,
    InsertionDeviceEnergy,
    InsertionDevicePolarisation,
    LookupTableColumnConfig,
    UndulatorGap,
    UndulatorPhaseAxes,
)
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

devices = DeviceManager()


K07_CONF_CLIENT = ConfigServer(url="https://daq-config.diamond.ac.uk")

LOOK_UPTABLE_DIR = "/dls_sw/k07/software/gda/workspace_git/gda-diamond.git/configurations/k07/lookupTables/"
GAP_LOOKUP_FILE_NAME = "JIDEnergy2GapCalibrations.csv"
PHASE_LOOKUP_FILE_NAME = "JIDEnergy2PhaseCalibrations.csv"
K07_GRATING_COLUMNS = "Grating"
K07_PHASE_POLY_DEG_COLUMNS = ["0th-order"]

BL = get_beamline_name("k07")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


# Grating does not exist yet - this class is a placeholder for when it does
class Grating(StrictEnum):
    NO_GRATING = "No Grating"


# Grating does not exist yet - this class is a placeholder for when it does
@devices.factory(skip=True)
def pgm() -> PlaneGratingMonochromator:
    return PlaneGratingMonochromator(
        prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=Grating,
    )


# Insertion device does not exist yet - these classes are placeholders at the moment.
@devices.factory(skip=True)
def id_gap() -> UndulatorGap:
    return UndulatorGap(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
    )


# Insertion device does not exist yet - these classes are placeholders at the moment.
@devices.factory(skip=True)
def id_phase() -> UndulatorPhaseAxes:
    return UndulatorPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="RPQ1",
        top_inner="RPQ2",
        btm_inner="RPQ3",
        btm_outer="RPQ4",
    )


# Insertion device does not exist yet - these classes are placeholders at the moment.
@devices.factory(skip=True)
def id(
    id_gap: UndulatorGap, id_phase: UndulatorPhaseAxes
) -> Apple2[UndulatorPhaseAxes]:
    """K07 insertion device."""
    return Apple2[UndulatorPhaseAxes](
        id_gap=id_gap,
        id_phase=id_phase,
    )


# Insertion device does not exist yet - temporary use Apple2EnforceLHMoveController
@devices.factory(skip=True)
def id_controller(
    id: Apple2[UndulatorPhaseAxes],
) -> Apple2EnforceLHMoveController[UndulatorPhaseAxes]:
    """i21 insertion device controller."""
    return Apple2EnforceLHMoveController[UndulatorPhaseAxes](
        apple2=id,
        gap_energy_motor_lut=ConfigServerEnergyMotorLookup(
            lut_config=LookupTableColumnConfig(grating=K07_GRATING_COLUMNS),
            config_client=K07_CONF_CLIENT,
            path=Path(LOOK_UPTABLE_DIR, GAP_LOOKUP_FILE_NAME),
        ),
        phase_energy_motor_lut=ConfigServerEnergyMotorLookup(
            lut_config=LookupTableColumnConfig(
                grating=K07_GRATING_COLUMNS, poly_deg=K07_PHASE_POLY_DEG_COLUMNS
            ),
            config_client=K07_CONF_CLIENT,
            path=Path(LOOK_UPTABLE_DIR, GAP_LOOKUP_FILE_NAME),
        ),
        units="eV",
    )


# Insertion device does not exist yet - these classes are placeholders at the moment.
@devices.factory(skip=True)
def id_energy(
    id_controller: Apple2EnforceLHMoveController[UndulatorPhaseAxes],
) -> InsertionDeviceEnergy:
    return InsertionDeviceEnergy(id_controller)


# Insertion device does not exist yet - these classes are placeholders at the moment.
@devices.factory(skip=True)
def id_polarisation(
    id_controller: Apple2EnforceLHMoveController[UndulatorPhaseAxes],
) -> InsertionDevicePolarisation:
    return InsertionDevicePolarisation(id_controller)
