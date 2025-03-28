from unittest.mock import ANY, AsyncMock, MagicMock, call, patch

import pytest
from ophyd_async.core import (
    init_devices,
    soft_signal_r_and_setter,
)
from ophyd_async.testing import set_mock_value

from dodal.devices.oav.snapshots.snapshot import (
    Snapshot,
)
from dodal.devices.oav.snapshots.snapshot_with_grid import (
    SnapshotWithGrid,
    asyncio_save_image,
)


async def create_and_set_mock_signal_r(dtype, name, value):
    get, _ = soft_signal_r_and_setter(dtype, value, name=name)
    await get.connect(mock=True)
    return get


@pytest.fixture
async def snapshot() -> Snapshot:
    async with init_devices(mock=True):
        snapshot = Snapshot("", "fake_snapshot")
    set_mock_value(snapshot.directory, "/tmp/")
    set_mock_value(snapshot.filename, "test")
    set_mock_value(snapshot.url, "http://test.url")
    return snapshot


@pytest.fixture
async def grid_snapshot() -> SnapshotWithGrid:
    async with init_devices(mock=True):
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


@pytest.fixture
def mock_session_with_valid_response():
    with patch(
        "dodal.devices.areadetector.plugins.MJPG.ClientSession.get", autospec=True
    ) as mock_get:
        mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())
        mock_response.ok = True
        mock_response.read.return_value = b"TEST"
        yield mock_get


@pytest.fixture
def mock_image_open():
    with patch("dodal.devices.areadetector.plugins.MJPG.Image") as patch_image:
        mock_open = patch_image.open
        mock_open.return_value.__aenter__.return_value = b"TEST"
        yield mock_open


@patch("dodal.devices.areadetector.plugins.MJPG.aiofiles", autospec=True)
async def test_snapshot_correctly_triggered_and_saved(
    mock_aiofiles,
    mock_image_open,
    mock_session_with_valid_response,
    snapshot,
):
    mock_aio_open = mock_aiofiles.open
    mock_aio_open.return_value.__aenter__.return_value = (mock_file := AsyncMock())

    await snapshot.trigger()

    test_url = await snapshot.url.get_value()
    # Get called with an instance of the session and correct url
    mock_session_with_valid_response.assert_called_once_with(ANY, test_url)

    assert await snapshot.last_saved_path.get_value() == "/tmp/test.png"
    mock_aio_open.assert_called_once_with("/tmp/test.png", "wb")
    mock_file.write.assert_called_once()


@patch("dodal.devices.areadetector.plugins.MJPG.Path.mkdir")
@patch("dodal.devices.areadetector.plugins.MJPG.aiofiles", autospec=True)
async def test_given_directory_not_existing_when_snapshot_triggered_then_directory_created(
    mock_aiofiles,
    mock_mkdir,
    mock_image_open,
    mock_session_with_valid_response,
    snapshot,
):
    mock_aio_open = mock_aiofiles.open
    mock_aio_open.return_value.__aenter__.return_value = AsyncMock()

    # Set new directory and test that it's created
    set_mock_value(snapshot.directory, "new_dir")

    await snapshot.trigger()

    mock_mkdir.assert_called_once()


@patch(
    "dodal.devices.oav.snapshots.snapshot_with_grid.add_grid_border_overlay_to_image"
)
@patch("dodal.devices.oav.snapshots.snapshot_with_grid.add_grid_overlay_to_image")
@patch("dodal.devices.oav.snapshots.snapshot_with_grid.asyncio_save_image")
async def test_snapshot_with_grid_triggered_saves_image_and_draws_correct_grid(
    mock_save_grid,
    patch_add_grid,
    patch_add_border,
    mock_image_open,
    mock_session_with_valid_response,
    grid_snapshot,
):
    grid_snapshot._save_image = (mock_save := AsyncMock())

    await grid_snapshot.trigger()

    mock_save.assert_awaited_once()
    patch_add_border.assert_called_once_with(
        mock_image_open.return_value.__enter__.return_value, 100, 100, 50, 15, 10
    )
    patch_add_grid.assert_called_once_with(
        mock_image_open.return_value.__enter__.return_value, 100, 100, 50, 15, 10
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


@patch("dodal.devices.areadetector.plugins.MJPG.Image")
@patch("dodal.devices.areadetector.plugins.MJPG.aiofiles", autospec=True)
async def test_asyncio_save_image(mock_aiofiles, patch_image):
    mock_aio_open = mock_aiofiles.open
    mock_aio_open.return_value.__aenter__.return_value = (mock_file := AsyncMock())

    test_path = MagicMock(return_value="some_path/test_grid.png")
    await asyncio_save_image(patch_image, test_path)

    patch_image.save.assert_called_once()
    mock_aio_open.assert_called_once_with(test_path, "wb")
    mock_file.write.assert_called_once()
