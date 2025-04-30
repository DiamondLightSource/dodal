from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ophyd_async.core import init_devices
from PIL import Image

from dodal.devices.webcam import Webcam, create_placeholder_image


@pytest.fixture
async def webcam(RE) -> Webcam:
    async with init_devices(mock=True):
        webcam = Webcam("", "", "")
    return webcam


async def test_given_last_saved_path_when_device_read_then_returns_path(webcam: Webcam):
    await webcam.last_saved_path.set("test")
    read = await webcam.read()
    assert read["webcam-last_saved_path"]["value"] == "test"


@pytest.mark.parametrize(
    "directory, filename, expected_path",
    [
        ("/tmp", "test", "/tmp/test.png"),
        ("/tmp/", "other", "/tmp/other.png"),
    ],
)
@patch("dodal.devices.webcam.aiofiles", autospec=True)
@patch("dodal.devices.webcam.ClientSession.get", autospec=True)
async def test_given_filename_and_directory_when_trigger_and_read_then_returns_expected_path(
    mock_get: MagicMock,
    mock_aiofiles,
    directory,
    filename,
    expected_path,
    webcam: Webcam,
):
    mock_get.return_value.__aenter__.return_value = AsyncMock()
    await webcam.filename.set(filename)
    await webcam.directory.set(directory)
    await webcam.trigger()
    read = await webcam.read()
    assert read["webcam-last_saved_path"]["value"] == expected_path


@patch("dodal.devices.webcam.aiofiles", autospec=True)
@patch("dodal.devices.webcam.ClientSession.get", autospec=True)
async def test_given_data_returned_from_url_when_trigger_then_data_written(
    mock_get: MagicMock, mock_aiofiles, webcam: Webcam
):
    mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())
    mock_response.read.return_value = (test_web_data := "TEST")
    mock_open = mock_aiofiles.open
    mock_open.return_value.__aenter__.return_value = (mock_file := AsyncMock())
    await webcam.filename.set("file")
    await webcam.directory.set("/tmp")
    await webcam.trigger()
    mock_open.assert_called_once_with("/tmp/file.png", "wb")
    mock_file.write.assert_called_once_with(test_web_data)


@patch("dodal.devices.webcam.ClientSession.get", autospec=True)
async def test_given_response_has_bad_status_but_response_read_still_returns_then_still_write_data(
    mock_get: MagicMock, webcam: Webcam
):
    mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())
    mock_response.ok = MagicMock(return_value=False)
    mock_response.read.return_value = (test_web_data := b"TEST")

    webcam._write_image = (mock_write := AsyncMock())

    await webcam.filename.set("file")
    await webcam.directory.set("/tmp")
    await webcam.trigger()

    mock_write.assert_called_once_with("/tmp/file.png", test_web_data)


@patch("dodal.devices.webcam.create_placeholder_image", autospec=True)
@patch("dodal.devices.webcam.ClientSession.get", autospec=True)
async def test_given_response_read_fails_then_placeholder_image_written(
    mock_get: MagicMock, mock_placeholder_image: MagicMock, webcam: Webcam
):
    mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())
    mock_response.read = AsyncMock(side_effect=Exception())
    mock_placeholder_image.return_value = (test_placeholder_data := b"TEST")

    webcam._write_image = (mock_write := AsyncMock())

    await webcam.filename.set("file")
    await webcam.directory.set("/tmp")
    await webcam.trigger()

    mock_write.assert_called_once_with("/tmp/file.png", test_placeholder_data)


def test_create_place_holder_image_gives_expected_bytes():
    image_bytes = create_placeholder_image()
    placeholder_image = Image.open(BytesIO(image_bytes))
    assert placeholder_image.width == 1024
    assert placeholder_image.height == 768
