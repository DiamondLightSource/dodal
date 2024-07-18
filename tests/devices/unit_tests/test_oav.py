from unittest.mock import AsyncMock, MagicMock, call, patch

import numpy as np
import pytest
from bluesky import plan_stubs as bps
from bluesky.run_engine import RunEngine
from ophyd.sim import instantiate_fake_device, make_fake_device
from ophyd_async.core import set_mock_value
from PIL import Image
from requests import HTTPError, Response

import dodal.devices.oav.utils as oav_utils
from dodal.devices.oav.oav_detector import OAV, OAVConfigParams
from dodal.devices.oav.pin_image_recognition import PinTipDetection
from dodal.devices.oav.pin_image_recognition.utils import SampleLocation
from dodal.devices.oav.utils import (
    PinNotFoundException,
    get_move_required_so_that_beam_is_at_pixel,
    wait_for_tip_to_be_found,
)
from dodal.devices.smargon import Smargon

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


@pytest.mark.parametrize(
    "px_per_um, beam_centre, angle, pixel_to_move_to, expected_xyz",
    [
        # Simple case of beam being in the top left and each pixel being 1 mm
        ([1000, 1000], [0, 0], 0, [100, 190], [100, 190, 0]),
        ([1000, 1000], [0, 0], -90, [50, 250], [50, 0, 250]),
        ([1000, 1000], [0, 0], 90, [-60, 450], [-60, 0, -450]),
        # Beam offset
        ([1000, 1000], [100, 100], 0, [100, 100], [0, 0, 0]),
        ([1000, 1000], [100, 100], -90, [50, 250], [-50, 0, 150]),
        # Pixels_per_micron different
        ([10, 50], [0, 0], 0, [100, 190], [1, 9.5, 0]),
        ([60, 80], [0, 0], -90, [50, 250], [3, 0, 20]),
    ],
)
def test_values_for_move_so_that_beam_is_at_pixel(
    smargon: Smargon,
    fake_oav: OAV,
    px_per_um,
    beam_centre,
    angle,
    pixel_to_move_to,
    expected_xyz,
):
    fake_oav.parameters.micronsPerXPixel = px_per_um[0]
    fake_oav.parameters.micronsPerYPixel = px_per_um[1]
    fake_oav.parameters.beam_centre_i = beam_centre[0]
    fake_oav.parameters.beam_centre_j = beam_centre[1]

    set_mock_value(smargon.omega.user_readback, angle)

    RE = RunEngine(call_returns_result=True)
    pos = RE(
        get_move_required_so_that_beam_is_at_pixel(
            smargon, pixel_to_move_to, fake_oav.parameters
        )
    ).plan_result

    assert pos == pytest.approx(expected_xyz)


@pytest.mark.asyncio
async def test_given_tip_found_when_wait_for_tip_to_be_found_called_then_tip_immediately_returned():
    mock_pin_tip_detect: PinTipDetection = instantiate_fake_device(
        PinTipDetection, name="pin_detect"
    )
    await mock_pin_tip_detect.connect(mock=True)
    mock_pin_tip_detect._get_tip_and_edge_data = AsyncMock(
        return_value=SampleLocation(100, 100, np.array([]), np.array([]))
    )
    RE = RunEngine(call_returns_result=True)
    result = RE(wait_for_tip_to_be_found(mock_pin_tip_detect))
    assert result.plan_result == (100, 100)  # type: ignore
    mock_pin_tip_detect._get_tip_and_edge_data.assert_called_once()


@pytest.mark.asyncio
async def test_given_no_tip_when_wait_for_tip_to_be_found_called_then_exception_thrown():
    mock_pin_tip_detect: PinTipDetection = instantiate_fake_device(
        PinTipDetection, name="pin_detect"
    )
    await mock_pin_tip_detect.connect(mock=True)
    await mock_pin_tip_detect.validity_timeout.set(0.2)
    mock_pin_tip_detect._get_tip_and_edge_data = AsyncMock(
        return_value=SampleLocation(
            *PinTipDetection.INVALID_POSITION, np.array([]), np.array([])
        )
    )
    RE = RunEngine(call_returns_result=True)
    with pytest.raises(PinNotFoundException):
        RE(wait_for_tip_to_be_found(mock_pin_tip_detect))
