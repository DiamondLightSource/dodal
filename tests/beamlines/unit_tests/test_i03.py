from dodal.beamlines import i03
from dodal.common.beamlines import beamline_utils


def test_list():
    i03.s4_slit_gaps(connect_immediately=True, mock=True)
    assert beamline_utils.list_active_devices() == ["s4_slit_gaps"]
    beamline_utils.clear_devices()
    assert beamline_utils.list_active_devices() == []
