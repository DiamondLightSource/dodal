from dodal.beamlines import i19_1, i19_2
from dodal.common.beamlines import beamline_utils


def test_list_1():
    i19_1.zebra(connect_immediately=True, mock=True)
    i19_1.oav(connect_immediately=True, mock=True)
    assert beamline_utils.list_active_devices() == ["zebra", "oav"]
    beamline_utils.clear_devices()
    assert beamline_utils.list_active_devices() == []


def test_list_2():
    i19_2.zebra(connect_immediately=True, mock=True)
    i19_2.shutter(connect_immediately=True, mock=True)
    assert beamline_utils.list_active_devices() == ["zebra", "shutter"]
    beamline_utils.clear_devices()
    assert beamline_utils.list_active_devices() == []
