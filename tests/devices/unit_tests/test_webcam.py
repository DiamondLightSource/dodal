from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bluesky.run_engine import RunEngine

from dodal.beamlines import i03
from dodal.devices.webcam import Webcam


@pytest.fixture
def webcam() -> Webcam:
    RunEngine()
    return i03.webcam(fake_with_ophyd_sim=True)


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


@patch("dodal.devices.webcam.aiofiles", autospec=True)
@patch("dodal.devices.webcam.ClientSession.get", autospec=True)
async def test_given_response_throws_exception_when_trigger_then_exception_rasied(
    mock_get: MagicMock, mock_aiofiles, webcam: Webcam
):
    class MyException(Exception):
        pass

    def _raise():
        raise MyException()

    mock_get.return_value.__aenter__.return_value = (mock_response := AsyncMock())
    mock_response.raise_for_status = _raise
    await webcam.filename.set("file")
    await webcam.directory.set("/tmp")
    with pytest.raises(MyException):
        await webcam.trigger()
