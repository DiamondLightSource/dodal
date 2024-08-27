import os

from dodal.common.beamlines import beamline_utils
from dodal.devices.i22.nxsas import NXSasOAV

os.environ["BEAMLINE"] = "p38"
from dodal.beamlines import i22


def test_devices_diff_when_in_lab():
    beamline_utils.clear_devices()
    saxs = i22.saxs(wait_for_connection=False, fake_with_ophyd_sim=True)
    assert saxs.__class__ == NXSasOAV, f"Expected NXSasOav, got {saxs.__class__}"
