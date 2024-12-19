from dodal.common.beamlines.beamline_utils import device_factory
from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.turbo_slit import TurboSlit
from dodal.devices.xspress3.xspress3 import Xspress3
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i20-1")
PREFIX = BeamlinePrefix(BL, suffix="J")
set_log_beamline(BL)
set_utils_beamline(BL)


@device_factory()
def turbo_slit() -> TurboSlit:
    """
    turboslit for selecting energy from the polychromator
    """

    return TurboSlit(f"{PREFIX.beamline_prefix}-OP-PCHRO-01:TS:")


@device_factory()
def xspress3() -> Xspress3:
    """
    16 channels Xspress3 detector
    """

    return Xspress3(
        f"{PREFIX.beamline_prefix}-EA-DET-03:",
        num_channels=16,
    )
