import asyncio
from unittest.mock import MagicMock, patch

import numpy as np
from ophyd_async.core import set_mock_value

from dodal.devices.oav.pin_image_recognition import MxSampleDetect, PinTipDetection
from dodal.devices.oav.pin_image_recognition.utils import SampleLocation

EVENT_LOOP = asyncio.new_event_loop()


DEVICE_NAME = "pin_tip_detection"
TRIGGERED_TIP_READING = DEVICE_NAME + "-triggered_tip"
TRIGGERED_TOP_EDGE_READING = DEVICE_NAME + "-triggered_top_edge"
TRIGGERED_BOTTOM_EDGE_READING = DEVICE_NAME + "-triggered_bottom_edge"


async def _get_pin_tip_detection_device() -> PinTipDetection:
    device = PinTipDetection("-DI-OAV-01", name=DEVICE_NAME)
    await device.connect(mock=True)
    return device


async def test_pin_tip_detect_can_be_connected_in_sim_mode():
    device = await _get_pin_tip_detection_device()
    await device.connect(mock=True)


async def test_soft_parameter_defaults_are_correct():
    device = await _get_pin_tip_detection_device()

    assert await device.validity_timeout.get_value() == 5.0
    assert await device.canny_lower_threshold.get_value() == 50
    assert await device.canny_upper_threshold.get_value() == 100
    assert await device.close_ksize.get_value() == 5
    assert await device.close_iterations.get_value() == 5
    assert await device.min_tip_height.get_value() == 5
    assert await device.scan_direction.get_value() == 1
    assert await device.preprocess_operation.get_value() == 10
    assert await device.preprocess_iterations.get_value() == 5
    assert await device.preprocess_ksize.get_value() == 5


async def test_numeric_soft_parameters_can_be_changed():
    device = await _get_pin_tip_detection_device()

    await device.validity_timeout.set(100.0)
    await device.canny_lower_threshold.set(5)
    await device.canny_upper_threshold.set(10)
    await device.close_ksize.set(15)
    await device.close_iterations.set(20)
    await device.min_tip_height.set(25)
    await device.scan_direction.set(-1)
    await device.preprocess_operation.set(2)
    await device.preprocess_ksize.set(3)
    await device.preprocess_iterations.set(4)

    assert await device.validity_timeout.get_value() == 100.0
    assert await device.canny_lower_threshold.get_value() == 5
    assert await device.canny_upper_threshold.get_value() == 10
    assert await device.close_ksize.get_value() == 15
    assert await device.close_iterations.get_value() == 20
    assert await device.min_tip_height.get_value() == 25
    assert await device.scan_direction.get_value() == -1
    assert await device.preprocess_operation.get_value() == 2
    assert await device.preprocess_ksize.get_value() == 3
    assert await device.preprocess_iterations.get_value() == 4


async def test_invalid_processing_func_uses_identity_function():
    device = await _get_pin_tip_detection_device()
    test_sample_location = SampleLocation(100, 200, np.array([]), np.array([]))

    set_mock_value(device.preprocess_operation, 50)  # Invalid index

    with (
        patch.object(MxSampleDetect, "__init__", return_value=None) as mock_init,
        patch.object(MxSampleDetect, "processArray", return_value=test_sample_location),
    ):
        await device._get_tip_and_edge_data(np.array([]))

        mock_init.assert_called_once()

        captured_func = mock_init.call_args[1]["preprocess"]

    # Assert captured preprocess function is the identitiy function
    arg = object()
    assert arg == captured_func(arg)


async def test_given_valid_data_reading_then_used_to_find_location():
    device = await _get_pin_tip_detection_device()
    image_array = np.array([1, 2, 3])
    test_sample_location = SampleLocation(
        100, 200, np.array([1, 2, 3]), np.array([4, 5, 6])
    )
    set_mock_value(device.array_data, image_array)

    with (
        patch.object(MxSampleDetect, "__init__", return_value=None),
        patch.object(
            MxSampleDetect, "processArray", return_value=test_sample_location
        ) as mock_process_array,
    ):
        await device.trigger()
        location = await device.read()

        process_call = mock_process_array.call_args[0][0]
        assert np.array_equal(process_call, image_array)
        assert location[TRIGGERED_TIP_READING]["value"] == (100, 200)
        assert np.all(
            location[TRIGGERED_TOP_EDGE_READING]["value"] == np.array([1, 2, 3])
        )
        assert np.all(
            location[TRIGGERED_BOTTOM_EDGE_READING]["value"] == np.array([4, 5, 6])
        )
        assert location[TRIGGERED_TIP_READING]["timestamp"] > 0


async def test_given_find_tip_fails_when_triggered_then_tip_invalid():
    device = await _get_pin_tip_detection_device()
    await device.validity_timeout.set(0.1)
    set_mock_value(device.array_data, np.array([1, 2, 3]))

    with (
        patch.object(MxSampleDetect, "__init__", return_value=None),
        patch.object(MxSampleDetect, "processArray", side_effect=Exception()),
    ):
        await device.trigger()
        reading = await device.read()
        assert reading[TRIGGERED_TIP_READING]["value"] == device.INVALID_POSITION
        assert len(reading[TRIGGERED_TOP_EDGE_READING]["value"]) == 0
        assert len(reading[TRIGGERED_BOTTOM_EDGE_READING]["value"]) == 0


@patch("dodal.devices.oav.pin_image_recognition.observe_value")
async def test_given_find_tip_fails_twice_when_triggered_then_tip_invalid_and_tried_twice(
    mock_image_read,
):
    async def get_array_data(_):
        yield np.array([1, 2, 3])
        yield np.array([1, 2])
        await asyncio.sleep(100)

    mock_image_read.side_effect = get_array_data
    device = await _get_pin_tip_detection_device()
    await device.validity_timeout.set(0.1)

    with (
        patch.object(MxSampleDetect, "__init__", return_value=None),
        patch.object(
            MxSampleDetect, "processArray", side_effect=Exception()
        ) as mock_process_array,
    ):
        await device.trigger()
        reading = await device.read()
        assert reading[TRIGGERED_TIP_READING]["value"] == device.INVALID_POSITION
        assert mock_process_array.call_count > 1


@patch("dodal.devices.oav.pin_image_recognition.LOGGER.warn")
@patch("dodal.devices.oav.pin_image_recognition.observe_value")
async def test_given_tip_invalid_then_loop_keeps_retrying_until_valid(
    mock_image_read: MagicMock,
    mock_logger: MagicMock,
):
    async def get_array_data(_):
        yield np.array([1, 2, 3])
        yield np.array([1, 2])
        await asyncio.sleep(100)

    mock_image_read.side_effect = get_array_data
    device = await _get_pin_tip_detection_device()

    class FakeLocation:
        def __init__(self, tip_x, tip_y, edge_top, edge_bottom):
            self.tip_x = tip_x
            self.tip_y = tip_y
            self.edge_top = edge_top
            self.edge_bottom = edge_bottom

    fake_top_edge = np.array([1, 2, 3])
    fake_bottom_edge = np.array([4, 5, 6])

    with (
        patch.object(MxSampleDetect, "__init__", return_value=None),
        patch.object(
            MxSampleDetect,
            "processArray",
            side_effect=[
                FakeLocation(None, None, fake_top_edge, fake_bottom_edge),
                FakeLocation(1, 1, fake_top_edge, fake_bottom_edge),
            ],
        ),
    ):
        await device.trigger()
        mock_logger.assert_called_once()
