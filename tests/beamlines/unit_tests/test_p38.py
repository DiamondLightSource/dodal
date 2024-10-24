import os

import pytest

from dodal.common.beamlines import beamline_utils
from dodal.devices.i22.nxsas import NXSasOAV

os.environ["BEAMLINE"] = "p38"
from dodal.beamlines import i22


def test_devices_diff_when_in_lab():
    beamline_utils.clear_devices()
    saxs = i22.saxs()
    assert saxs.__class__ == NXSasOAV, f"Expected NXSasOav, got {saxs.__class__}"


@pytest.mark.parametrize("module_and_devices_for_beamline", ["i22"], indirect=True)
def test_device_creation(RE, module_and_devices_for_beamline):
    _, devices = module_and_devices_for_beamline
    saxs = devices["saxs"]  # type: ignore

    assert saxs.drv.trigger_mode.name == "BL22I-DI-DICAM-03:DET:TriggerMode"
