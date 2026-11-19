from ophyd_async.epics.adcore import ADAcquireLogic

from dodal.beamlines.i05_shared import devices as i05_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i05_1 import XYZAzimuthPolarDefocusStage
from dodal.devices.beamlines.i05_shared import (
    LensMode,
    Mj7j8Mirror,
    PassEnergy,
    PolynomialCompoundMovable,
)
from dodal.devices.common_mirror import XYZPiezoSwitchingMirror
from dodal.devices.electron_analyser.base import (
    ElectronAnalyserTriggerLogic,
    RegionLogic,
)
from dodal.devices.electron_analyser.mbs import (
    EntranceSlitInformationDevice,
    MbsAnalyserDriverIO,
    MbsDetector,
)
from dodal.devices.hutch_shutter import HutchShutter
from dodal.devices.motors import XYZPitchYawRollStage
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

"""AKA Nano branch line."""

BL = get_beamline_name("i05-1")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()
devices.include(i05_shared_devices)


@devices.factory()
def mj7j8() -> XYZPiezoSwitchingMirror:
    return XYZPiezoSwitchingMirror(
        prefix=f"{PREFIX.beamline_prefix}-OP-RFM-01:",
        mirrors=Mj7j8Mirror,
    )


# Same as i05, but with different configured values
@devices.factory
def m1mj6_pitch(
    m1: XYZPitchYawRollStage, m3mj6: XYZPiezoSwitchingMirror
) -> PolynomialCompoundMovable:
    """Virtual mirror, moves m1 rotations and mj6 displacements in linear dependence to
    maintain the beam on mj6 centre.
    """
    return PolynomialCompoundMovable(
        master=m1.pitch, slave=m3mj6.x, offset=6.75958, step=-0.0104762
    )


# Same as i05, but with different configured values
@devices.factory
def m1es_pitch(
    m1mj6_pitch: PolynomialCompoundMovable, m3mj6: XYZPiezoSwitchingMirror
) -> PolynomialCompoundMovable:
    """Virtual mirror, moves m1 rotations, mj6 displacements and rotations in linear
    dependence on m1 to maintain the beam on the exit slit.
    """
    return PolynomialCompoundMovable(
        master=m1mj6_pitch, slave=m3mj6.pitch, offset=5005, step=0.27
    )


@devices.factory()
def nano_shutter() -> HutchShutter:
    return HutchShutter(PREFIX.beamline_prefix)


@devices.factory
def sm() -> XYZAzimuthPolarDefocusStage:
    """Sample Manipulator."""
    return XYZAzimuthPolarDefocusStage(prefix=f"{PREFIX.beamline_prefix}-EA-SM-01:")


@devices.factory
def analyser_slits() -> EntranceSlitInformationDevice:
    return EntranceSlitInformationDevice(f"{PREFIX.beamline_prefix}-EA-SLITS-01:POS")


@devices.factory
def analyser(
    pgm: PlaneGratingMonochromator, analyser_slits: EntranceSlitInformationDevice
) -> MbsDetector[LensMode, PassEnergy]:
    prefix = f"{PREFIX.beamline_prefix}-EA-DET-04:CAM:"
    driver = MbsAnalyserDriverIO(prefix, LensMode, PassEnergy)
    return MbsDetector[LensMode, PassEnergy](
        prefix,
        driver,
        acquire_logic=ADAcquireLogic(driver),
        trigger_logic=ElectronAnalyserTriggerLogic(driver),
        region_logic=RegionLogic(driver, pgm.energy.user_readback),
        config_sigs=(
            analyser_slits.direction,
            analyser_slits.size,
            analyser_slits.shape,
            analyser_slits.aperture,
        ),
    )
