from dodal.beamlines import i03
from dodal.common.beamlines import beamline_utils


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
