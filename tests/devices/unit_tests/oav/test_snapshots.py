from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ophyd_async.core import DeviceCollector, MockSignalBackend, SignalR, set_mock_value

from dodal.devices.oav.snapshots.snapshot_with_beam_centre import SnapshotWithBeamCentre


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
    return snapshot


@patch("dodal.devices.areadetector.plugins.MJPG_async.Path.mkdir")
@patch("dodal.devices.areadetector.plugins.MJPG_async.Image")
@patch("dodal.devices.oav.snapshots.snapshot_with_beam_centre.ImageDraw")
@patch(
    "dodal.devices.areadetector.plugins.MJPG_async.ClientSession.get",
    autospec=True,
)
@patch("dodal.devices.areadetector.plugins.MJPG_async.aiofiles", autospec=True)
async def test_given_snapshot_triggered_then_crosshair_drawn_and_file_saved(
    mock_aiofiles, mock_get, patch_image_draw, patch_image, mock_mkdir, snapshot
):
    mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())
    mock_response.ok = MagicMock(return_value=True)
    mock_response.read.return_value = (test_data := b"TEST")

    mock_aio_open = mock_aiofiles.open
    mock_aio_open.return_value.__aenter__.return_value = (mock_file := AsyncMock())

    patch_line = MagicMock()
    patch_image_draw.Draw.return_value.line = patch_line

    mock_open = patch_image.open
    mock_open.return_value.__aenter__.return_value = test_data

    await snapshot.directory.set("/tmp/")
    await snapshot.filename.set("test")

    await snapshot.trigger()

    assert len(patch_line.mock_calls) == 2
    assert await snapshot.last_saved_path.get_value() == "/tmp/test.png"
    mock_aio_open.assert_called_once_with("/tmp/test.png", "wb")
    mock_file.write.assert_called_once()
