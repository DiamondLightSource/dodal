from dodal.device_manager import DeviceManager
from dodal.devices.i05.enums import Grating
from dodal.devices.insertion_device import (
    Apple2,
    UndulatorGap,
    UndulatorLockedPhaseAxes,
)
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.synchrotron import Synchrotron
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i05-shared")
PREFIX = BeamlinePrefix("i05-shared", "I")

devices = DeviceManager()


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def pgm() -> PlaneGratingMonochromator:
    return PlaneGratingMonochromator(
        prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=Grating,
    )


@devices.factory()
def id_gap() -> UndulatorGap:
    return UndulatorGap(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


@devices.factory()
def id_phase() -> UndulatorLockedPhaseAxes:
    return UndulatorLockedPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="PL",
        btm_inner="PU",
    )


@devices.factory()
def id(
    id_gap: UndulatorGap,
    id_phase: UndulatorLockedPhaseAxes,
) -> Apple2[UndulatorLockedPhaseAxes]:
    """i05 insertion device."""
    return Apple2[UndulatorLockedPhaseAxes](id_gap=id_gap, id_phase=id_phase)
