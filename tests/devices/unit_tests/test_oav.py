from unittest.mock import MagicMock, patch

import pytest
from ophyd.sim import make_fake_device

from dodal.devices.oav.oav_detector import OAV, OAVConfigParams

DISPLAY_CONFIGURATION = "tests/devices/unit_tests/test_display.configuration"
ZOOM_LEVELS_XML = "tests/devices/unit_tests/test_jCameraManZoomLevels.xml"


@pytest.fixture
def fake_oav() -> OAV:
    oav_params = OAVConfigParams(ZOOM_LEVELS_XML, DISPLAY_CONFIGURATION)
    FakeOAV = make_fake_device(OAV)
    fake_oav: OAV = FakeOAV(name="test fake OAV", params=oav_params)

    fake_oav.grid_snapshot.url.sim_put("http://test.url")  # type: ignore
    fake_oav.grid_snapshot.filename.put("test filename")
    fake_oav.grid_snapshot.directory.put("test directory")
    fake_oav.grid_snapshot.top_left_x.put(100)
    fake_oav.grid_snapshot.top_left_y.put(100)
    fake_oav.grid_snapshot.box_width.put(50)
    fake_oav.grid_snapshot.num_boxes_x.put(15)
    fake_oav.grid_snapshot.num_boxes_y.put(10)
    fake_oav.grid_snapshot.x_size.sim_put(1024)  # type: ignore
    fake_oav.grid_snapshot.y_size.sim_put(768)  # type: ignore

    fake_oav.cam.port_name.sim_put("CAM")  # type: ignore
    fake_oav.proc.port_name.sim_put("PROC")  # type: ignore

    fake_oav.wait_for_connection()
    fake_oav.zoom_controller.set("1.0x").wait()

    return fake_oav


@pytest.fixture
def mock_get_with_valid_response():
    patcher = patch("requests.get")
    mock_get = patcher.start()
    mock_get.return_value.content = b""
    yield mock_get
    patcher.stop()


@patch("dodal.devices.areadetector.plugins.MJPG.Image")
@patch("dodal.devices.areadetector.plugins.MJPG.os", new=MagicMock())
def test_snapshot_trigger_loads_correct_url(
    mock_image: MagicMock, mock_get_with_valid_response: MagicMock, fake_oav: OAV
):
    st = fake_oav.grid_snapshot.trigger()
    st.wait()
    mock_get_with_valid_response.assert_called_once_with("http://test.url", stream=True)


@patch("dodal.devices.areadetector.plugins.MJPG.Image.open")
@patch("dodal.devices.areadetector.plugins.MJPG.os")
def test_given_directory_not_existing_when_snapshot_triggered_then_directory_created(
    mock_os, mock_open: MagicMock, mock_get_with_valid_response, fake_oav
):
    mock_os.path.isdir.return_value = False
    st = fake_oav.grid_snapshot.trigger()
    st.wait()
    mock_os.mkdir.assert_called_once_with("test directory")
