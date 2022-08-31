from unittest import skip
from dodal.devices.detector import DetectorParams
from dodal.devices.fast_grid_scan import FastGridScan
from dodal.devices.motors import I03Smargon
from dodal.devices.zebra import Zebra
from dodal.devices.undulator import Undulator
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.slit_gaps import SlitGaps
from dodal.devices.eiger import EigerDetector
from dodal.devices.detector import DetectorParams
from dodal.utils import skip_connection_test

BEAMLINE_PREFIX = "BL03S"
INSERTION_PREFIX = "SR03S"

def fast_grid_scan() -> FastGridScan:
    return FastGridScan(name="fast_grid_scan", prefix=f"{BEAMLINE_PREFIX}-MO-SGON-01:FGS:")

def zebra() -> Zebra:
    return Zebra(name="zebra", prefix=f"{BEAMLINE_PREFIX}-EA-ZEBRA-01:")

def undulator() -> Undulator:
    return Undulator(name="undulator", prefix=f"{INSERTION_PREFIX}-MO-SERVC-01:")

def synchrotron() -> Synchrotron:
    return Synchrotron(name="synchrotron")

def slit_gaps() -> SlitGaps:
    return SlitGaps(name="slit_gaps", prefix=f"{BEAMLINE_PREFIX}-AL-SLITS-04:")

def sample_motors() -> I03Smargon:
    return I03Smargon(name="sample_motors", prefix=f"{BEAMLINE_PREFIX}-MO-SGON-01:")

@skip_connection_test() # Currently eiger doesn't have all the expected PVs
def eiger(parameters: DetectorParams) -> EigerDetector:
    return EigerDetector(parameters, prefix=f"{BEAMLINE_PREFIX}-EA-EIGER-01:")
