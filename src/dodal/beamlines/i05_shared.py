from dodal.device_manager import DeviceManager
from dodal.devices.apple2_undulator import (
    Apple2,
    UndulatorGap,
    UndulatorLockedPhaseAxes,
)
from dodal.devices.i05.enums import Grating
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.synchrotron import Synchrotron
from dodal.utils import BeamlinePrefix

devices = DeviceManager()

PREFIX = BeamlinePrefix("i05", "I")


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
def id() -> Apple2[UndulatorLockedPhaseAxes]:
    """i05 insertion device."""
    return Apple2[UndulatorLockedPhaseAxes](id_gap=id_gap(), id_phase=id_phase())
