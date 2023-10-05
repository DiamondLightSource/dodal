import asyncio
from unittest.mock import patch

import pytest
from ophyd_async.core import set_sim_value

from dodal.devices.oav.pin_image_recognition import MxSampleDetect, PinTipDetection

EVENT_LOOP = asyncio.new_event_loop()


pytest_plugins = ("pytest_asyncio",)


async def _get_pin_tip_detection_device() -> PinTipDetection:
    device = PinTipDetection("-DI-OAV-01")
    await device.connect(sim=True)
    return device


@pytest.mark.asyncio
async def test_pin_tip_detect_can_be_connected_in_sim_mode():
    device = await _get_pin_tip_detection_device()
    await device.connect(sim=True)


@pytest.mark.asyncio
async def test_soft_parameter_defaults_are_correct():
    device = await _get_pin_tip_detection_device()

    assert await device.timeout.get_value() == 10.0
    assert await device.canny_lower.get_value() == 50
    assert await device.canny_upper.get_value() == 100
    assert await device.close_ksize.get_value() == 5
    assert await device.close_iterations.get_value() == 5
    assert await device.min_tip_height.get_value() == 5
    assert await device.scan_direction.get_value() == 1
    assert await device.preprocess.get_value() == 10
    assert await device.preprocess_iterations.get_value() == 5
    assert await device.preprocess_ksize.get_value() == 5


@pytest.mark.asyncio
async def test_numeric_soft_parameters_can_be_changed():
    device = await _get_pin_tip_detection_device()

    await device.timeout.set(100.0)
    await device.canny_lower.set(5)
    await device.canny_upper.set(10)
    await device.close_ksize.set(15)
    await device.close_iterations.set(20)
    await device.min_tip_height.set(25)
    await device.scan_direction.set(-1)
    await device.preprocess.set(2)
    await device.preprocess_ksize.set(3)
    await device.preprocess_iterations.set(4)

    assert await device.timeout.get_value() == 100.0
    assert await device.canny_lower.get_value() == 5
    assert await device.canny_upper.get_value() == 10
    assert await device.close_ksize.get_value() == 15
    assert await device.close_iterations.get_value() == 20
    assert await device.min_tip_height.get_value() == 25
    assert await device.scan_direction.get_value() == -1
    assert await device.preprocess.get_value() == 2
    assert await device.preprocess_ksize.get_value() == 3
    assert await device.preprocess_iterations.get_value() == 4


@pytest.mark.asyncio
async def test_invalid_processing_func_uses_identity_function():
    device = await _get_pin_tip_detection_device()

    set_sim_value(device.preprocess, 50)  # Invalid index

    with patch.object(
        MxSampleDetect, "__init__", return_value=None
    ) as mock_init, patch.object(
        MxSampleDetect, "processArray", return_value=((None, None), None)
    ):
        await device.read()

        mock_init.assert_called_once()

        captured_func = mock_init.call_args[1]["preprocess"]

    # Assert captured preprocess function is the identitiy function
    arg = object()
    assert arg == captured_func(arg)
