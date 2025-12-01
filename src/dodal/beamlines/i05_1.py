from ophyd_async.core import StrictEnum

from dodal.beamline_specific_utils.i05_shared import (
    m1_collimating_mirror,
    m3mj6_switching_mirror,
    pgm,
)
from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.i05.common_mirror import XYZPiezoSwitchingMirror
from dodal.devices.motors import XYZPitchYawRollStage
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i05-1")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def pgm() -> PlaneGratingMonochromator:
    return i05_pgm()


@device_factory()
def m1() -> XYZPitchYawRollStage:
    return m1_collimating_mirror()


@device_factory()
def m3mj6() -> XYZPiezoSwitchingMirror:
    return m3mj6_switching_mirror()


# beamline specific devices


# will connect after https://jira.diamond.ac.uk/browse/I05-731
class Mj7j8Mirror(StrictEnum):
    UNKNOWN = "Unknown"
    MJ8 = "MJ8"
    MJ7 = "MJ7"
    REFERENCE = "Reference"


# will connect after https://jira.diamond.ac.uk/browse/I05-731
@device_factory()
def mj7j8() -> XYZPiezoSwitchingMirror:
    return XYZPiezoSwitchingMirror(
        prefix=f"{PREFIX.beamline_prefix}-OP-RFM-01:",
        mirrors=Mj7j8Mirror,
    )
