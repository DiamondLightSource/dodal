from dodal.beamlines.i05_shared import devices as i05_shared_devices
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.beamlines.i05_1 import XYZAzimuthPolarDefocusStage
from dodal.devices.beamlines.i05_shared import LensMode, Mj7j8Mirror, PassEnergy
from dodal.devices.common_mirror import XYZPiezoSwitchingMirror
from dodal.devices.electron_analyser.mbs import (
    EntranceSlitInformationDevice,
    MbsDetector,
)
from dodal.devices.hutch_shutter import HutchShutter
from dodal.devices.pgm import PlaneGratingMonochromator
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i05-1")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)

devices = DeviceManager()
devices.include(i05_shared_devices)


# will connect after https://jira.diamond.ac.uk/browse/I05-731
@devices.factory(skip=True)
def mj7j8() -> XYZPiezoSwitchingMirror:
    return XYZPiezoSwitchingMirror(
        prefix=f"{PREFIX.beamline_prefix}-OP-RFM-01:",
        mirrors=Mj7j8Mirror,
    )


@devices.factory()
def nano_shutter() -> HutchShutter:
    return HutchShutter(PREFIX.beamline_prefix)


@devices.factory
def sm() -> XYZAzimuthPolarDefocusStage:
    """Sample Manipulator."""
    return XYZAzimuthPolarDefocusStage(prefix=f"{PREFIX.beamline_prefix}-EA-SM-01:")


# Note: Currently fails. Requires https://jira.diamond.ac.uk/browse/I05-764
@devices.factory
def analyser_slits() -> EntranceSlitInformationDevice:
    return EntranceSlitInformationDevice(f"{PREFIX.beamline_prefix}-EA-SLITS-01:POS")


@devices.factory
def analyser(
    pgm: PlaneGratingMonochromator, analyser_slits: EntranceSlitInformationDevice
) -> MbsDetector[LensMode, PassEnergy]:
    config_sigs = (
        analyser_slits.direction,
        analyser_slits.size,
        analyser_slits.shape,
        analyser_slits.setting,
    )
    return MbsDetector[LensMode, PassEnergy](
        prefix=f"{PREFIX.beamline_prefix}-EA-DET-04:CAM:",
        lens_mode_type=LensMode,
        pass_energy_type=PassEnergy,
        energy_source=pgm.energy.user_readback,
        config_sigs=config_sigs,
    )
