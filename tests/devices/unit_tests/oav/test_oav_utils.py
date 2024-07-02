from pathlib import Path
from unittest.mock import MagicMock

from PIL.Image import Image

from dodal.devices.oav.utils import save_thumbnail


def test_given_full_sized_image_when_save_thumbnail_called_then_saves_with_expected_size_and_location():
    mock_image = MagicMock(spec=Image)
    mock_image.size = (400, 200)
    full_path = Path("/test/path.jpg")
    save_thumbnail(full_path, mock_image, 10)
    mock_image.thumbnail.assert_called_once_with((20, 10))
    mock_image.save.assert_called_once_with("/test/patht.jpg")
