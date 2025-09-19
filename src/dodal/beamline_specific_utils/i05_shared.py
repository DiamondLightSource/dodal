from ophyd_async.core import StrictEnum

from dodal.common.beamlines.beamline_utils import device_factory
from dodal.devices.i05.common_mirror import XYZPiezoSwitchingMirror
from dodal.devices.motors import XYZPitchYawRollStage
from dodal.devices.pgm import PGM
from dodal.utils import BeamlinePrefix

PREFIX = BeamlinePrefix("i05", "I")


class M3MJ6Mirror(StrictEnum):
    UNKNOWN = "Unknown"
    MJ6 = "MJ6"
    M3 = "M3"
    REFERENCE = "Reference"


class Grating(StrictEnum):
    PT_400 = "400 lines/mm"
    C_1600 = "C 1600 lines/mm"
    RH_1600 = "Rh 1600 lines/mm"
    PT_800 = "B 800 lines/mm"


@device_factory()
def pgm() -> PGM:
    return PGM(prefix=f"{PREFIX.beamline_prefix}-OP-PGM-01:", grating=Grating)


@device_factory()
def m1_collimating_mirror() -> XYZPitchYawRollStage:
    return XYZPitchYawRollStage(prefix=f"{PREFIX.beamline_prefix}-OP-COL-01:")


@device_factory()
def m3mj6_switching_mirror() -> XYZPiezoSwitchingMirror:
    return XYZPiezoSwitchingMirror(
        prefix=f"{PREFIX.beamline_prefix}-OP-SWTCH-01:",
        mirrors=M3MJ6Mirror,
    )
