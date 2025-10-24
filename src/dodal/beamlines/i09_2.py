from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.apple2_undulator import (
    Apple2,
    UndulatorGap,
    UndulatorPhaseAxes,
)
from dodal.devices.i09.enums import Grating
from dodal.devices.pgm import PGM
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i09-2")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@device_factory()
def pgm() -> PGM:
    return PGM(prefix=f"{PREFIX.beamline_prefix}-MO-PGM-01:", grating=Grating)


@device_factory()
def jid_gap() -> UndulatorGap:
    return UndulatorGap(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


@device_factory()
def jid_phase() -> UndulatorPhaseAxes:
    return UndulatorPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="PUO",
        top_inner="PUI",
        btm_inner="PLI",
        btm_outer="PLO",
    )


@device_factory()
def jid() -> Apple2:
    """I09 soft x-ray insertion device."""
    return Apple2(
        id_gap=jid_gap(),
        id_phase=jid_phase(),
    )
