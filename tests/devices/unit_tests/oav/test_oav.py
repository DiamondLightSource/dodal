from unittest.mock import AsyncMock, patch

import pytest
from ophyd_async.testing import set_mock_value

from dodal.devices.oav.oav_detector import (
    OAV,
    Cam,
    ZoomController,
)


async def test_zoom_controller():
    zoom_controller = ZoomController("", "zoom_controller")
    await zoom_controller.connect(mock=True)
    zoom_controller.level.describe = AsyncMock(
        return_value={"zoom_controller-level": {"choices": ["1.0x", "3.0x"]}}
    )
    status = zoom_controller.set("3.0x")
    await status
    assert status.success
    assert await zoom_controller.level.get_value() == "3.0x"


async def test_cam():
    cam = Cam("", "fake cam")
    await cam.connect(mock=True)
    set_mock_value(cam.array_size_x, 1024)
    set_mock_value(cam.array_size_y, 768)

    status = cam.acquire_period.set(0.01)
    await status
    assert status.success
    assert await cam.acquire_period.get_value() == 0.01

    status = cam.acquire_time.set(0.01)
    await status
    assert status.success
    assert await cam.acquire_time.get_value() == 0.01

    assert await cam.array_size_x.get_value() == 1024


@pytest.mark.parametrize(
    "zoom_level,expected_microns_x,expected_microns_y",
    [
        ("1.0x", 2.87, 2.87),
        ("2.5", 2.31, 2.31),
        ("5.0x", 1.58, 1.58),
        ("15.0", 0.302, 0.302),
    ],
)
async def test_get_micronsperpixel_from_oav(
    zoom_level, expected_microns_x, expected_microns_y, oav: OAV
):
    set_mock_value(oav.zoom_controller.level, zoom_level)

    assert await oav.microns_per_pixel_x.get_value() == pytest.approx(
        expected_microns_x, abs=1e-2
    )
    assert await oav.microns_per_pixel_y.get_value() == pytest.approx(
        expected_microns_y, abs=1e-2
    )


@pytest.mark.parametrize(
    "zoom_level,expected_xCentre,expected_yCentre",
    [("1.0", 477, 359), ("5.0", 517, 350), ("10.0x", 613, 344)],
)
async def test_extract_beam_position_given_different_zoom_levels(
    zoom_level,
    expected_xCentre,
    expected_yCentre,
    oav: OAV,
):
    set_mock_value(oav.zoom_controller.level, zoom_level)

    assert await oav.beam_centre_i.get_value() == expected_xCentre
    assert await oav.beam_centre_j.get_value() == expected_yCentre


async def test_oav_returns_rescaled_beam_position_and_microns_per_pixel_correctly(
    oav: OAV,
):
    set_mock_value(oav.grid_snapshot.x_size, 1292)
    set_mock_value(oav.grid_snapshot.y_size, 964)

    set_mock_value(oav.zoom_controller.level, "1.0")

    microns_x = await oav.microns_per_pixel_x.get_value()
    microns_y = await oav.microns_per_pixel_y.get_value()
    beam_x = await oav.beam_centre_i.get_value()
    beam_y = await oav.beam_centre_j.get_value()

    assert microns_x == pytest.approx(2.27, abs=1e-2)
    assert microns_y == pytest.approx(2.28, abs=1e-2)
    assert beam_x == 601
    assert beam_y == 450


@patch(
    "dodal.devices.areadetector.plugins.MJPG.ClientSession.get",
    autospec=True,
)
@patch("dodal.devices.areadetector.plugins.MJPG.Image")
async def test_when_snapshot_triggered_post_processing_called_correctly(
    patch_image, mock_get, oav: OAV
):
    mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())
    mock_response.ok = True
    mock_response.read.return_value = (test_data := b"TEST")

    mock_open = patch_image.open
    mock_open.return_value.__aenter__.return_value = test_data

    oav.snapshot.post_processing = (mock_proc := AsyncMock())

    await oav.snapshot.trigger()

    mock_proc.assert_awaited_once()
