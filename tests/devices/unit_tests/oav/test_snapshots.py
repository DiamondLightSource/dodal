from pathlib import Path
from unittest.mock import ANY, AsyncMock, MagicMock, call, patch

import pytest
from ophyd_async.core import DeviceCollector, MockSignalBackend, SignalR, set_mock_value
from PIL import Image

from dodal.devices.oav.snapshots.snapshot_with_beam_centre import SnapshotWithBeamCentre
from dodal.devices.oav.snapshots.snapshot_with_grid import SnapshotWithGrid


def create_and_set_mock_signal_r(dtype, name, value):
    sig = SignalR(MockSignalBackend(dtype), name=name)
    set_mock_value(sig, value)
    return sig


@pytest.fixture
async def snapshot() -> SnapshotWithBeamCentre:
    mock_beam_x = create_and_set_mock_signal_r(int, "moxk_beam_x", 510)
    mock_beam_y = create_and_set_mock_signal_r(int, "mock_beam_y", 380)
    async with DeviceCollector(mock=True):
        snapshot = SnapshotWithBeamCentre("", mock_beam_x, mock_beam_y, "fake_snapshot")
    set_mock_value(snapshot.directory, "/tmp/")
    set_mock_value(snapshot.filename, "test")
    set_mock_value(snapshot.url, "http://test.url")
    return snapshot


@pytest.fixture
async def grid_snapshot() -> SnapshotWithGrid:
    async with DeviceCollector(mock=True):
        grid_snapshot = SnapshotWithGrid("", "fake_grid")

    set_mock_value(grid_snapshot.top_left_x, 100)
    set_mock_value(grid_snapshot.top_left_y, 100)
    set_mock_value(grid_snapshot.box_width, 50)
    set_mock_value(grid_snapshot.num_boxes_x, 15)
    set_mock_value(grid_snapshot.num_boxes_y, 10)

    set_mock_value(grid_snapshot.directory, "/tmp/")
    set_mock_value(grid_snapshot.filename, "test")
    set_mock_value(grid_snapshot.url, "http://test.url")
    return grid_snapshot


@patch("dodal.devices.areadetector.plugins.MJPG.Image")
@patch("dodal.devices.oav.snapshots.snapshot_with_beam_centre.ImageDraw")
@patch(
    "dodal.devices.areadetector.plugins.MJPG.ClientSession.get",
    autospec=True,
)
async def test_snapshot_with_beam_centre_triggered_then_crosshair_drawn_and(
    mock_get, patch_image_draw, patch_image, snapshot
):
    mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())
    mock_response.ok = MagicMock(return_value=True)
    mock_response.read.return_value = (test_data := b"TEST")

    patch_line = MagicMock()
    patch_image_draw.Draw.return_value.line = patch_line

    snapshot._save_image = (mock_save := AsyncMock())

    mock_open = patch_image.open
    mock_open.return_value.__aenter__.return_value = test_data

    await snapshot.trigger()

    assert len(patch_line.mock_calls) == 2
    mock_save.assert_awaited_once()


@patch("dodal.devices.areadetector.plugins.MJPG.Path.mkdir")
@patch("dodal.devices.areadetector.plugins.MJPG.Image")
@patch(
    "dodal.devices.areadetector.plugins.MJPG.ClientSession.get",
    autospec=True,
)
@patch("dodal.devices.areadetector.plugins.MJPG.aiofiles", autospec=True)
async def test_snapshot_with_beam_centre_correctly_triggered_and_saved(
    mock_aiofiles, mock_get, patch_image, mock_mkdir, snapshot
):
    mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())
    mock_response.ok = MagicMock(return_value=True)
    mock_response.read.return_value = (test_data := b"TEST")

    mock_aio_open = mock_aiofiles.open
    mock_aio_open.return_value.__aenter__.return_value = (mock_file := AsyncMock())

    mock_open = patch_image.open
    mock_open.return_value.__aenter__.return_value = test_data

    await snapshot.trigger()

    assert await snapshot.last_saved_path.get_value() == "/tmp/test.png"
    mock_aio_open.assert_called_once_with("/tmp/test.png", "wb")
    mock_file.write.assert_called_once()


def test_snapshot_draws_expected_crosshair(tmp_path: Path):
    image = Image.open("tests/test_data/test_images/oav_snapshot_test.png")
    SnapshotWithBeamCentre.draw_crosshair(image, 510, 380)
    image.save(tmp_path / "output_image.png")
    expected_image = Image.open("tests/test_data/test_images/oav_snapshot_expected.png")
    image_bytes = image.tobytes()
    expected_bytes = expected_image.tobytes()
    assert image_bytes == expected_bytes, "Actual and expected images differ"


@patch("dodal.devices.areadetector.plugins.MJPG.Image")
@patch(
    "dodal.devices.oav.snapshots.snapshot_with_grid.add_grid_border_overlay_to_image"
)
@patch("dodal.devices.oav.snapshots.snapshot_with_grid.add_grid_overlay_to_image")
@patch(
    "dodal.devices.areadetector.plugins.MJPG.ClientSession.get",
    autospec=True,
)
async def test_snapshot_with_grid_triggered_saves_image_and_draws_correct_grid(
    mock_get, patch_add_grid, patch_add_border, patch_image, grid_snapshot
):
    mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())
    mock_response.ok = MagicMock(return_value=True)
    mock_response.read.return_value = (test_data := b"TEST")

    mock_open = patch_image.open
    mock_open.return_value.__aenter__.return_value = test_data

    grid_snapshot._save_image = (mock_save := AsyncMock())
    grid_snapshot._save_grid_to_image = (mock_save_grid := AsyncMock())

    await grid_snapshot.trigger()

    test_url = await grid_snapshot.url.get_value()
    # Get called with an instance of the session and correct url
    mock_get.assert_called_once_with(ANY, test_url)
    mock_save.assert_awaited_once()
    patch_add_border.assert_called_once_with(
        mock_open.return_value.__enter__.return_value, 100, 100, 50, 15, 10
    )
    patch_add_grid.assert_called_once_with(
        mock_open.return_value.__enter__.return_value, 100, 100, 50, 15, 10
    )
    assert mock_save_grid.await_count == 2
    expected_grid_save_calls = [
        call(ANY, f"/tmp/test_{suffix}.png")
        for suffix in ["outer_overlay", "grid_overlay"]
    ]
    assert mock_save_grid.mock_calls == expected_grid_save_calls
    assert (
        await grid_snapshot.last_path_outer.get_value() == "/tmp/test_outer_overlay.png"
    )
    assert (
        await grid_snapshot.last_path_full_overlay.get_value()
        == "/tmp/test_grid_overlay.png"
    )
