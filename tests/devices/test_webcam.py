import pathlib
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from ophyd_async.core import init_devices
from PIL import Image
from yarl import URL

from dodal.devices.webcam import Webcam, create_placeholder_image


@pytest.fixture
async def webcam() -> Webcam:
    async with init_devices(mock=True):
        webcam = Webcam(URL("http://example.com"))
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
@patch("dodal.devices.webcam.Image.open")
async def test_given_filename_and_directory_when_trigger_and_read_then_returns_expected_path(
    mock_image_open,
    mock_get: MagicMock,
    mock_aiofiles,
    directory,
    filename,
    expected_path,
    webcam: Webcam,
):
    img_byte_arr = BytesIO()
    Image.new("RGB", (10, 10)).save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    mock_response = AsyncMock()
    mock_response.read.return_value = img_bytes
    mock_get.return_value.__aenter__.return_value = mock_response

    await webcam.filename.set(filename)
    await webcam.directory.set(directory)
    await webcam.trigger()
    read = await webcam.read()
    assert read["webcam-last_saved_path"]["value"] == expected_path


@patch("dodal.devices.webcam.aiofiles", autospec=True)
@patch("dodal.devices.webcam.ClientSession.get", autospec=True)
@patch("dodal.devices.webcam.Image.open")
async def test_given_data_returned_from_url_when_trigger_then_data_written(
    mock_image_open, mock_get: MagicMock, mock_aiofiles, webcam: Webcam
):
    mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())
    mock_response.read.return_value = (test_web_data := b"TEST")
    mock_open = mock_aiofiles.open
    mock_open.return_value.__aenter__.return_value = (mock_file := AsyncMock())
    await webcam.filename.set("file")
    await webcam.directory.set("/tmp")
    await webcam.trigger()
    mock_open.assert_called_once_with("/tmp/file.png", "wb")
    mock_file.write.assert_called_once_with(test_web_data)


@patch("dodal.devices.webcam.ClientSession.get", autospec=True)
@patch("dodal.devices.webcam.Image.open")
async def test_given_response_has_bad_status_but_response_read_still_returns_then_still_write_data(
    mock_image_open, mock_get: MagicMock, webcam: Webcam
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


@patch("dodal.devices.webcam.aiofiles", autospec=True)
@patch("dodal.devices.webcam.create_placeholder_image", autospec=True)
@patch("dodal.devices.webcam.ClientSession.get", autospec=True)
@patch("dodal.devices.webcam.Image.open")
async def test_given_non_image_error_from_webcam_then_placeholder_image_written(
    mock_image_open,
    mock_get: MagicMock,
    mock_placeholder_image: MagicMock,
    mock_aiofiles,
    webcam: Webcam,
):
    mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())
    # This can occur when the camera gets an internal error
    mock_response.read.return_value = b"<html><h1>503 Service Unavailable</h1></html>"

    mock_image = MagicMock()
    mock_image.verify.side_effect = Exception("Invalid image")
    mock_image_open.return_value = mock_image
    mock_placeholder_image.return_value = (test_placeholder_data := b"TEST")

    mock_open = mock_aiofiles.open
    mock_open.return_value.__aenter__.return_value = (mock_file := AsyncMock())

    await webcam.filename.set("file")
    await webcam.directory.set("/tmp")
    await webcam.trigger()

    mock_image.verify.assert_called_once()
    mock_open.assert_called_once_with("/tmp/file.png", "wb")
    mock_file.write.assert_called_once_with(test_placeholder_data)


@pytest.mark.skip(reason="System test that hits a real webcam, not suitable for CI")
async def test_webcam_system_test(RE):
    async with init_devices():
        webcam = Webcam(
            url=URL("http://i03-webcam1/axis-cgi/jpg/image.cgi"),
        )

    this_folder = pathlib.Path(__file__).parent.resolve()

    await webcam.filename.set("test")
    await webcam.directory.set(str(this_folder))
    await webcam.trigger()


def test_create_place_holder_image_gives_expected_bytes():
    image_bytes = create_placeholder_image()
    placeholder_image = Image.open(BytesIO(image_bytes))
    assert placeholder_image.width == 1024
    assert placeholder_image.height == 768
