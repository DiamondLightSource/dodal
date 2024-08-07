from unittest.mock import MagicMock

from dodal.beamlines import i03
from dodal.common.beamlines import beamline_utils
from dodal.devices.aperturescatterguard import ApertureScatterguard


def test_list():
    beamline_utils.clear_devices()
    i03.zebra(wait_for_connection=False, fake_with_ophyd_sim=True)
    i03.synchrotron(wait_for_connection=False, fake_with_ophyd_sim=True)
    i03.aperture_scatterguard(wait_for_connection=False, fake_with_ophyd_sim=True)
    assert beamline_utils.list_active_devices() == [
        "zebra",
        "synchrotron",
        "aperture_scatterguard",
    ]


def test_getting_second_aperture_scatterguard_gives_valid_device(RE):
    beamline_utils.clear_devices()
    test_positions = MagicMock()
    ap_sg: ApertureScatterguard = i03.aperture_scatterguard(
        fake_with_ophyd_sim=True, aperture_positions=test_positions
    )
    assert ap_sg.aperture_positions is not None
    ap_sg = i03.aperture_scatterguard(fake_with_ophyd_sim=True)
    assert ap_sg.aperture_positions == test_positions
