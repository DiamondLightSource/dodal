from ophyd_async.core import StrictEnum

from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.apple2_undulator import (
    Apple2,
    InsertionDeviceEnergy,
    InsertionDevicePolarisation,
    UndulatorGap,
    UndulatorPhaseAxes,
)
from dodal.devices.k07 import K07Apple2Controller
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("k07")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


# Grating does not exist yet - this class is a placeholder for when it does
class Grating(StrictEnum):
    NO_GRATING = "No Grating"


# Insertion device objects


# Insertion device gap and phase do not exist yet - these classes are placeholders for when they do
@device_factory(skip=True)
def id_gap() -> UndulatorGap:
    return UndulatorGap(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
    )


@device_factory(skip=True)
def id_phase() -> UndulatorPhaseAxes:
    return UndulatorPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="RPQ1",
        top_inner="RPQ2",
        btm_inner="RPQ3",
        btm_outer="RPQ4",
    )


# Insertion device raw does not exist yet - this class is a placeholder for when it does
@device_factory(skip=True)
def id() -> Apple2:
    return Apple2(
        id_gap=id_gap(),
        id_phase=id_phase(),
    )


# Insertion device controller does not exist yet - this class is a placeholder for when it does
@device_factory(skip=True)
def id_controller() -> K07Apple2Controller:
    return K07Apple2Controller(apple2=id())


# Insertion device energy does not exist yet - this class is a placeholder for when it does
@device_factory(skip=True)
def id_energy() -> InsertionDeviceEnergy:
    return InsertionDeviceEnergy(id_controller=id_controller())


@device_factory(skip=True)
def id_polarisation() -> InsertionDevicePolarisation:
    return InsertionDevicePolarisation(id_controller=id_controller())


# Grating does not exist yet - this class is a placeholder for when it does
@device_factory(skip=True)
def pgm() -> PlaneGratingMonochromator:
    return PlaneGratingMonochromator(
        prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=Grating,
    )
