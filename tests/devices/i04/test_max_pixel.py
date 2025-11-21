from unittest.mock import patch

import cv2
import numpy as np
import pytest

from dodal.devices.i04.max_pixel import MaxPixel


@pytest.fixture
def mock_array():
    # Return a NumPy array (not a list) so cv2 works correctly
    return np.array(
        [[0, 29, 60, 80], [100, 100, 110, 200], [100, 100, 110, 200], [0, 50, 50, 50]],
        dtype=np.uint8,
    )


def test_preprocessed_data_grayscale_and_blur(mock_array):
    device = MaxPixel("TEST:")
    # Monkeypatch array_data to be our mock array
    device.array_data = cv2.cvtColor(  # type: ignore
        np.stack([mock_array] * 3, axis=-1),  # make it 3-channel BGR
        cv2.COLOR_BGR2GRAY,
    )
    blurred = device.preprocessed_data()
    assert isinstance(blurred, np.ndarray)
    assert blurred.shape == mock_array.shape


def test_trigger_sets_max_pixel_val():
    # Create a simple mock array
    mock_array = np.array(
        [[0, 29, 60, 80], [100, 100, 110, 200], [100, 100, 110, 200], [0, 50, 50, 50]],
        dtype=np.uint8,
    )

    # Make it 3-channel so cv2.COLOR_BGR2GRAY works
    mock_image = np.stack([mock_array] * 3, axis=-1)

    # Patch the class attribute `array_data` to return our mock image
    with patch.object(MaxPixel, "array_data", mock_image):  # type: ignore
        device = MaxPixel("TEST:")
        device.trigger()

        # After trigger, max_pixel_val should be set to 200
        assert device.max_pixel_val.get() == 200  # type: ignore
