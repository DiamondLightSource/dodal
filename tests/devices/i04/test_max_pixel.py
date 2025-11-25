from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import cv2
import numpy as np
import pytest
from ophyd_async.core import init_devices

from dodal.devices.i04.max_pixel import MaxPixel

# @pytest.fixture
# async def max_pixel() -> AsyncGenerator[tuple[MaxPixel, MagicMock], None]:
#     async with init_devices(mock=True):
#         # mock_ap_sg = MagicMock()
#         # mock_ap_sg.return_value.selected_aperture.set = AsyncMock()
#         # mock_ap_sg.return_value.selected_aperture.get_value = AsyncMock()
#         max_pixel = MaxPixel(
#             prefix="",
#             name="test_scin",
#         )
#         max_pixel.
# with ExitStack() as motor_patch_stack:
#     for motor in [scintillator.y_mm, scintillator.z_mm]:
#         motor_patch_stack.enter_context(patch_motor(motor))
#     await scintillator.y_mm.set(5)
#     await scintillator.z_mm.set(5)
#     yield scintillator, mock_ap_sg


@pytest.fixture
def mock_array():
    # Return a NumPy array (not a list) so cv2 works correctly
    return np.array(
        [[0, 29, 60, 80], [100, 100, 110, 200], [100, 100, 110, 200], [0, 50, 50, 50]],
        dtype=np.uint8,
    )


async def test_preprocessed_data_grayscale_and_blur(mock_array):
    device = MaxPixel("TEST:")
    # Monkeypatch array_data to be our mock array
    mock_array_signal = Mock()
    mock_array_signal.get_value = mock_array

    # device.array_data.get_value = cv2.cvtColor(  # type: ignore
    #     np.stack([mock_array] * 3, axis=-1),  # make it 3-channel BGR
    #     cv2.COLOR_BGR2GRAY,
    # )

    blurred = await device.preprocessed_data()
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
