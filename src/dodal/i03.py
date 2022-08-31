from dodal.devices.detector import DetectorParams
from dodal.devices.fast_grid_scan import FastGridScan
from dodal.devices.motors import I03Smargon
from dodal.devices.zebra import Zebra
from dodal.devices.undulator import Undulator
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.slit_gaps import SlitGaps
from dodal.devices.eiger import EigerDetector
from dodal.devices.detector import DetectorParams

BEAMLINE_PREFIX = "BL03I"
INSERTION_PREFIX = "SR03I"

def fast_grid_scan() -> FastGridScan: 
    return FastGridScan(f"{BEAMLINE_PREFIX}-MO-SGON-01:FGS:")

def zebra() -> Zebra:
    return Zebra(f"{BEAMLINE_PREFIX}-EA-ZEBRA-01:")

def undulator() -> Undulator:
    return Undulator(f"{INSERTION_PREFIX}-MO-SERVC-01:")

def synchrotron() -> Synchrotron:
    return Synchrotron()

def slit_gaps() -> SlitGaps:
    return SlitGaps(f"{BEAMLINE_PREFIX}-AL-SLITS-04:")

def sample_motors() -> I03Smargon:
    return I03Smargon(f"{BEAMLINE_PREFIX}-MO-SGON-01:")

def eiger(parameters: DetectorParams) -> EigerDetector:
    return EigerDetector(parameters, prefix=f"{BEAMLINE_PREFIX}-EA-EIGER-01:")
