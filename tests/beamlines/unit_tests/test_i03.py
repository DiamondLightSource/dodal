from dodal.beamlines import i03
from dodal.common.beamlines import beamline_utils


def test_list():
    i03.s4_slit_gaps(wait_for_connection=True, fake_with_ophyd_sim=True)
    assert beamline_utils.list_active_devices() == ["s4_slit_gaps"]
    beamline_utils.clear_devices()
    assert beamline_utils.list_active_devices() == []
