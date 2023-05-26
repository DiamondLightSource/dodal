import pytest
from ophyd import Device
from ophyd.sim import FakeEpicsSignal

from dodal.beamlines import beamline_utils, i03
from dodal.devices.aperturescatterguard import AperturePositions, ApertureScatterguard
from dodal.devices.smargon import Smargon
from dodal.devices.zebra import Zebra
from dodal.utils import make_all_devices
