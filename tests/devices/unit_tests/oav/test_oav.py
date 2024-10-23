from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from ophyd_async.core import set_mock_value

from dodal.devices.oav.oav_detector import OAV, ZoomController


async def test_zoom_controller():
    zoom_controller = ZoomController("", "fake zoom controller")
    await zoom_controller.connect(mock=True)
    status = zoom_controller.set("3.0x")
    await status
    assert status.success
    assert await zoom_controller.level.get_value() == "3.0x"


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
async def test_snapshot_trigger_handles_bad_request_status(mock_get, oav: OAV):
    mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())
    mock_response.ok = False

    with pytest.raises(aiohttp.ClientConnectionError):
        await oav.grid_snapshot.trigger()
