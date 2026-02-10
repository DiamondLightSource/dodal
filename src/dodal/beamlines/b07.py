from dodal.beamlines.b07_shared import devices as b07_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.b07 import Grating, LensMode, PsuMode
from dodal.devices.beamlines.b07.b07_motors import B07SampleManipulator52B
from dodal.devices.electron_analyser.base import EnergySource
from dodal.devices.electron_analyser.specs import SpecsDetector
from dodal.devices.motors import XYZPolarStage
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("b07")
B_PREFIX = BeamlinePrefix(BL, suffix="B")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()
devices.include(b07_shared_devices)


@devices.factory()
def pgm() -> PlaneGratingMonochromator:
    return PlaneGratingMonochromator(
        prefix=f"{B_PREFIX.beamline_prefix}-OP-PGM-01:",
        grating=Grating,
    )


@devices.factory()
def energy_source(pgm: PlaneGratingMonochromator) -> EnergySource:
    return EnergySource(pgm.energy.user_readback)


# CAM:IMAGE will fail to connect outside the beamline network,
# see https://github.com/DiamondLightSource/dodal/issues/1852
@devices.factory(mock=True)
def analyser(energy_source: EnergySource) -> SpecsDetector[LensMode, PsuMode]:
    return SpecsDetector[LensMode, PsuMode](
        prefix=f"{B_PREFIX.beamline_prefix}-EA-DET-01:CAM:",
        lens_mode_type=LensMode,
        psu_mode_type=PsuMode,
        energy_source=energy_source,
    )


@devices.factory()
def sm52b() -> B07SampleManipulator52B:
    return B07SampleManipulator52B(prefix=f"{B_PREFIX.beamline_prefix}-EA-SM-52:")


@devices.factory()
def sm21b() -> XYZPolarStage:
    """Sample manipulator. NOTE: The polar attribute is equivalent to GDA roty."""
    return XYZPolarStage(
        prefix=f"{B_PREFIX.beamline_prefix}-EA-SM-21:", polar_infix="ROTY"
    )
