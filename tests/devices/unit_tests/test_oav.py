from unittest.mock import MagicMock, call, patch

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd.sim import make_fake_device
from PIL import Image
from requests import HTTPError, Response

import dodal.devices.oav.utils as oav_utils
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


@patch("requests.get")
def test_snapshot_trigger_handles_request_with_bad_status_code_correctly(
    mock_get, fake_oav: OAV
):
    response = Response()
    response.status_code = 404
    mock_get.return_value = response

    st = fake_oav.grid_snapshot.trigger()
    with pytest.raises(HTTPError):
        st.wait()


@patch("requests.get")
@patch("dodal.devices.areadetector.plugins.MJPG.Image")
@patch("dodal.devices.areadetector.plugins.MJPG.os", new=MagicMock())
def test_snapshot_trigger_loads_correct_url(
    mock_image: MagicMock, mock_get: MagicMock, fake_oav: OAV
):
    st = fake_oav.grid_snapshot.trigger()
    st.wait()
    mock_get.assert_called_once_with("http://test.url", stream=True)


@patch("requests.get")
@patch("dodal.devices.areadetector.plugins.MJPG.Image.open")
@patch("dodal.devices.areadetector.plugins.MJPG.os", new=MagicMock())
def test_snapshot_trigger_saves_to_correct_file(
    mock_open: MagicMock, mock_get, fake_oav
):
    image = Image.open("test")
    mock_open.return_value.__enter__.return_value = image
    with patch.object(image, "save") as mock_save:
        st = fake_oav.grid_snapshot.trigger()
        st.wait()
        expected_calls_to_save = [
            call(f"test directory/test filename{addition}.png")
            for addition in ["", "_outer_overlay", "_grid_overlay"]
        ]
        calls_to_save = mock_save.mock_calls
        assert calls_to_save == expected_calls_to_save


@patch("requests.get")
@patch("dodal.devices.areadetector.plugins.MJPG.Image.open")
@patch("dodal.devices.areadetector.plugins.MJPG.os")
def test_given_directory_not_existing_when_snapshot_triggered_then_directory_created(
    mock_os, mock_open: MagicMock, mock_get, fake_oav
):
    mock_os.path.isdir.return_value = False
    st = fake_oav.grid_snapshot.trigger()
    st.wait()
    mock_os.mkdir.assert_called_once_with("test directory")


@patch("requests.get")
@patch("dodal.devices.areadetector.plugins.MJPG.Image.open")
@patch("dodal.devices.areadetector.plugins.MJPG.os", new=MagicMock())
def test_snapshot_trigger_applies_current_microns_per_pixel_to_snapshot(
    mock_open: MagicMock, mock_get, fake_oav
):
    image = Image.open("test")  # type: ignore
    mock_open.return_value.__enter__.return_value = image

    expected_mpp_x = fake_oav.parameters.micronsPerXPixel
    expected_mpp_y = fake_oav.parameters.micronsPerYPixel
    with patch.object(image, "save"):
        st = fake_oav.grid_snapshot.trigger()
        st.wait()
        assert fake_oav.grid_snapshot.microns_per_pixel_x.get() == expected_mpp_x
        assert fake_oav.grid_snapshot.microns_per_pixel_y.get() == expected_mpp_y


@patch("requests.get")
@patch("dodal.devices.areadetector.plugins.MJPG.Image.open")
@patch("dodal.devices.oav.grid_overlay.add_grid_overlay_to_image")
@patch("dodal.devices.oav.grid_overlay.add_grid_border_overlay_to_image")
@patch("dodal.devices.areadetector.plugins.MJPG.os", new=MagicMock())
def test_correct_grid_drawn_on_image(
    mock_border_overlay: MagicMock,
    mock_grid_overlay: MagicMock,
    mock_open: MagicMock,
    mock_get: MagicMock,
    fake_oav: OAV,
):
    st = fake_oav.grid_snapshot.trigger()
    st.wait()
    expected_border_calls = [
        call(mock_open.return_value.__enter__.return_value, 100, 100, 50, 15, 10)
    ]
    expected_grid_calls = [
        call(mock_open.return_value.__enter__.return_value, 100, 100, 50, 15, 10)
    ]
    actual_border_calls = mock_border_overlay.mock_calls
    actual_grid_calls = mock_grid_overlay.mock_calls
    assert actual_border_calls == expected_border_calls
    assert actual_grid_calls == expected_grid_calls


def test_bottom_right_from_top_left():
    top_left = np.array([123, 123])
    bottom_right = oav_utils.bottom_right_from_top_left(
        top_left, 20, 30, 0.1, 0.15, 2.7027, 2.7027
    )
    assert bottom_right[0] == 863 and bottom_right[1] == 1788
    bottom_right = oav_utils.bottom_right_from_top_left(
        top_left, 15, 20, 0.005, 0.007, 1, 1
    )
    assert bottom_right[0] == 198 and bottom_right[1] == 263


def test_when_zoom_1_then_flat_field_applied(fake_oav: OAV, RE: RunEngine):
    RE(bps.abs_set(fake_oav.zoom_controller, "1.0x"))
    assert fake_oav.grid_snapshot.input_plugin.get() == "PROC"


def test_when_zoom_not_1_then_flat_field_removed(fake_oav: OAV, RE: RunEngine):
    RE(bps.abs_set(fake_oav.zoom_controller, "10.0x"))
    assert fake_oav.grid_snapshot.input_plugin.get() == "CAM"


def test_when_zoom_is_externally_changed_to_1_then_flat_field_not_changed(
    fake_oav: OAV,
):
    """This test is required to ensure that Hyperion doesn't cause unexpected behaviour
    e.g. change the flatfield when the zoom level is changed through the synoptic"""
    fake_oav.grid_snapshot.input_plugin.sim_put("CAM")  # type: ignore

    fake_oav.zoom_controller.level.sim_put("1.0x")  # type: ignore
    assert fake_oav.grid_snapshot.input_plugin.get() == "CAM"


def test_get_beam_position_from_zoom_only_called_once_on_multiple_connects(
    fake_oav: OAV,
):
    fake_oav.wait_for_connection()
    fake_oav.wait_for_connection()
    fake_oav.wait_for_connection()

    with (
        patch(
            "dodal.devices.oav.oav_detector.OAVConfigParams.update_on_zoom",
            MagicMock(),
        ),
        patch(
            "dodal.devices.oav.oav_detector.OAVConfigParams.get_beam_position_from_zoom",
            MagicMock(),
        ) as mock_get_beam_position_from_zoom,
        patch(
            "dodal.devices.oav.oav_detector.OAVConfigParams.load_microns_per_pixel",
            MagicMock(),
        ),
    ):
        fake_oav.zoom_controller.level.sim_put("2.0x")  # type: ignore
        assert mock_get_beam_position_from_zoom.call_count == 1
