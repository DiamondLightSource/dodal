import os

import pytest

from dodal.common.beamlines import beamline_utils
from dodal.devices.i22.nxsas import NXSasOAV

os.environ["BEAMLINE"] = "p38"
from dodal.beamlines import i22


def test_devices_diff_when_in_lab():
    beamline_utils.clear_devices()
    saxs = i22.saxs(wait_for_connection=False, fake_with_ophyd_sim=True)
    assert saxs.__class__ == NXSasOAV, f"Expected NXSasOav, got {saxs.__class__}"


# todo fix the following tests
# FAILED tests/beamlines/unit_tests/test_i03.py::test_list - KeyError: "No beamline parameter path found, maybe 'BEAMLINE' environment variable is not set!"
# FAILED tests/beamlines/unit_tests/test_p38.py::test_devices_diff_when_in_lab - AssertionError: Expected NXSasOav, got <class 'dodal.devices.i22.nxsas.NXSasPilatus'>
# assert <class 'dodal.devices.i22.nxsas.NXSasPilatus'> == NXSasOAV
#  +  where <class 'dodal.devices.i22.nxsas.NXSasPilatus'> = <dodal.devices.i22.nxsas.NXSasPilatus object at 0x7f016ca5b340>.__class__


@pytest.mark.parametrize("module_and_devices_for_beamline", ["p38"], indirect=True)
def test_device_creation(RE, module_and_devices_for_beamline):
    _, devices = module_and_devices_for_beamline
    saxs: NXSasOAV = devices["saxs"]  # type: ignore

    print(saxs)
    assert saxs.prefix == "BL24I-MO-VGON-01:"
    assert saxs.kappa.prefix == "BL24I-MO-VGON-01:KAPPA"
