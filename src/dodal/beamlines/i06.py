from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.insertion_device.apple2_undulator import (
    Apple2,
    UndulatorGap,
    UndulatorLockedPhaseAxes,
)
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i06")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def idd_gap() -> UndulatorGap:
    return UndulatorGap(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


@device_factory()
def idd_phase() -> UndulatorLockedPhaseAxes:
    return UndulatorLockedPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="PL",
        btm_inner="PU",
    )


@device_factory()
def idd() -> Apple2:
    """i06 downstream insertion device."""
    return Apple2(id_gap=idd_gap(), id_phase=idd_phase())


@device_factory()
def idu_gap() -> UndulatorGap:
    return UndulatorGap(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-21:")


@device_factory()
def idu_phase() -> UndulatorLockedPhaseAxes:
    return UndulatorLockedPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-21:",
        top_outer="PL",
        btm_inner="PU",
    )


@device_factory()
def idu() -> Apple2:
    """i06 upstream insertion device."""
    return Apple2(id_gap=idd_gap(), id_phase=idd_phase())
