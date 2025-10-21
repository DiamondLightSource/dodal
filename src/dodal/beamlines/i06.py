from dodal.beamline_specific_utils.i05_shared import pgm as i05_pgm
from dodal.common.beamlines.beamline_utils import (
    device_factory,
)
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.apple2_undulator import (
    Apple2,
    UndulatorGap,
    UndulatorLockedPhaseAxes,
)
from dodal.devices.pgm import PGM
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
def pgm() -> PGM:
    return i05_pgm()


@device_factory()
def id() -> Apple2:
    """i05 downstream insertion device:"""
    return Apple2(
        id_gap=UndulatorGap(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:"),
        id_phase=UndulatorLockedPhaseAxes(
            prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
            top_outer="PL",
            btm_inner="PU",
        ),
    )
