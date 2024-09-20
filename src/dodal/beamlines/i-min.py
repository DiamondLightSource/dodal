from ophyd_async.fastcs.panda import HDFPanda

from dodal.common.beamlines.beamline_utils import get_path_provider
from dodal.common.beamlines.device_factory import device_factory
from dodal.common.beamlines.device_helpers import numbered_slits
from dodal.devices.i22.fswitch import FSwitch
from dodal.devices.slits import Slits


@device_factory()
def fswitch() -> FSwitch:
    return FSwitch(
        prefix="-MO-FSWT-01:",
        lens_geometry="paraboloid",
        cylindrical=True,
        lens_material="Beryllium",
    )


@device_factory()
def slits_6() -> Slits:
    return numbered_slits(6)


@device_factory()
def panda1() -> HDFPanda:
    return HDFPanda(
        prefix="-EA-PANDA-01:",
        path_provider=get_path_provider(),
    )
