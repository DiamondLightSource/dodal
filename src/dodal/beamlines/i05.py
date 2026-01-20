from dodal.beamlines.i05_shared import devices as i05_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.insertion_device import (
    Apple2,
    UndulatorGap,
    UndulatorLockedPhaseAxes,
)
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.devices.temperture_controller import (
    Lakeshore336,
)
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

devices = DeviceManager()
devices.include(i05_devices)

BL = get_beamline_name("i05")
PREFIX = BeamlinePrefix(BL)
set_log_beamline(BL)
set_utils_beamline(BL)


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
    pgm: PlaneGratingMonochromator,
) -> Apple2:
    """i05 insertion device."""
    return Apple2(id_gap=id_gap, id_phase=id_phase)


@devices.factory()
def sample_temperature_controller() -> Lakeshore336:
    return Lakeshore336(prefix=f"{PREFIX.beamline_prefix}-EA-TCTRL-02:")
