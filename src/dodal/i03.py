# from dodal.devices.aperture import Aperture
# from dodal.devices.backlight import Backlight
from dodal.devices.DCM import DCM
from dodal.devices.detector import DetectorParams
from dodal.devices.eiger import EigerDetector

# from dodal.devices.fast_grid_scan import FastGridScan
# from dodal.devices.oav import OAV
# from dodal.devices.slit_gaps import SlitGaps
from dodal.devices.smargon import Smargon
from dodal.utils import BeamlinePrefix, get_beamline_name

# from dodal.devices.synchrotron import Synchrotron
# from dodal.devices.undulator import Undulator
# from dodal.devices.zebra import Zebra

BL = get_beamline_name("i03")


def dcm() -> DCM:
    return DCM(f"{BeamlinePrefix(BL).beamline_prefix}")


def eiger(params: DetectorParams) -> EigerDetector:
    return EigerDetector(
        params, prefix=f"{BeamlinePrefix(BL).beamline_prefix}-EA-EIGER-01:"
    )


def sample_motors() -> Smargon:
    return Smargon(
        name="sample_motors",
        prefix=f"{BeamlinePrefix(BL).beamline_prefix}-MO-SGON-01:",
    )
