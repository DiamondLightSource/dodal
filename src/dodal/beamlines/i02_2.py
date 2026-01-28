"""Beamline i02-2 is also known as VMXi, or I02I"""

from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.device_manager import DeviceManager
from dodal.devices.motors import XYStage
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import BeamlinePrefix, get_beamline_name

BL = get_beamline_name("i02-2")
PREFIX = BeamlinePrefix(BL, suffix="I")
set_log_beamline(BL)
set_utils_beamline(BL)
DAQ_CONFIGURATION_PATH = "/dls_sw/i02-2/software/daq_configuration"

devices = DeviceManager()


@devices.factory()
def synchrotron() -> Synchrotron:
    return Synchrotron()


@devices.factory()
def sample_motors() -> XYStage:
    return XYStage(f"{PREFIX.beamline_prefix}-MO-GONIO-01:SAMPLE:")
