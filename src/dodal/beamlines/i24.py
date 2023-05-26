from typing import Optional

from dodal.beamlines.beamline_utils import BL, device_instantiation
from dodal.devices.aperturescatterguard import AperturePositions, ApertureScatterguard
from dodal.devices.backlight import Backlight
from dodal.devices.DCM import DCM
from dodal.devices.detector import DetectorParams
from dodal.devices.detector_motion import DetectorMotion
from dodal.devices.eiger import EigerDetector
from dodal.devices.fast_grid_scan import FastGridScan
from dodal.devices.oav.oav_detector import OAV
from dodal.devices.s4_slit_gaps import S4SlitGaps
from dodal.devices.smargon import Smargon
from dodal.devices.synchrotron import Synchrotron
from dodal.devices.undulator import Undulator
from dodal.devices.zebra import Zebra
from dodal.utils import BeamlinePrefix, skip_device
