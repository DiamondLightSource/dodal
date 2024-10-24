
from dodal.beamlines import i22
from dodal.common.beamlines import beamline_utils
from dodal.devices.i22.nxsas import NXSasPilatus


def test_list():
    beamline_utils.clear_devices()
    i22.synchrotron()
    saxs = i22.saxs()
    assert (
        saxs.__class__ == NXSasPilatus
    ), f"Expected NXSasPilatus, got {saxs.__class__}"

    assert beamline_utils.list_active_devices() == ["synchrotron", "saxs"]
