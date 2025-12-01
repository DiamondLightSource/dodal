from ophyd_async.core import StrictEnum

from dodal.beamline_specific_utils.i05_shared import (
    m1_collimating_mirror,
    m3mj6_switching_mirror,
)
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
from dodal.devices.i05.common_mirror import XYZPiezoSwitchingMirror, XYZSwitchingMirror
from dodal.devices.motors import XYZPitchYawRollStage
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i05")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


# BL05 shared devices


@device_factory()
def m1() -> XYZPitchYawRollStage:
    return m1_collimating_mirror()


# will connect after https://jira.diamond.ac.uk/browse/I05-731
@device_factory(skip=True)
def m3mj6() -> XYZPiezoSwitchingMirror:
    return m3mj6_switching_mirror()


# beamline specific devices


class M4M5Mirror(StrictEnum):
    UNKNOWN = "Unknown"
    M4 = "M4"
    M5 = "M5"
    REFERENCE = "Reference"


# will connect after https://jira.diamond.ac.uk/browse/I05-731
@device_factory(skip=True)
def m4m5() -> XYZSwitchingMirror:
    return XYZSwitchingMirror(
        prefix=f"{PREFIX.beamline_prefix}-OP-RFM-01:",
        mirrors=M4M5Mirror,
    )


@device_factory()
def pgm() -> PlaneGratingMonochromator:
    return i05_pgm()


@device_factory()
def id_gap() -> UndulatorGap:
    return UndulatorGap(prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:")


@device_factory()
def id_phase() -> UndulatorLockedPhaseAxes:
    return UndulatorLockedPhaseAxes(
        prefix=f"{PREFIX.insertion_prefix}-MO-SERVC-01:",
        top_outer="PL",
        btm_inner="PU",
    )


@device_factory()
def id() -> Apple2:
    """i05 insertion device."""
    return Apple2(id_gap=id_gap(), id_phase=id_phase())
