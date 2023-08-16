import pytest
import numpy as np
from numpy.typing import NDArray
import asyncio
from dodal.devices.oav.pin_tip_detection.oav_with_pin_tip_detection import PinTipDetection, MxSampleDetect
from dodal.devices.oav.pin_tip_detection.pin_tip_detect_utils import SampleLocation, ArrayProcessingFunctions
from ophyd.v2.core import set_sim_value
from unittest.mock import MagicMock


EVENT_LOOP = asyncio.new_event_loop()


pytest_plugins = ('pytest_asyncio', )


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

    assert await device.timeout.get_value() == 10.
    assert await device.canny_lower.get_value() == 50
    assert await device.canny_upper.get_value() == 100
    assert await device.close_ksize.get_value() == 5
    assert await device.close_iterations.get_value() == 5
    assert await device.min_tip_height.get_value() == 5
    assert await device.scan_direction.get_value() == 1


@pytest.mark.asyncio
async def test_numeric_soft_parameters_can_be_changed():
    device = await _get_pin_tip_detection_device()

    await device.timeout.set(100.)
    await device.canny_lower.set(5)
    await device.canny_upper.set(10)
    await device.close_ksize.set(15)
    await device.close_iterations.set(20)
    await device.min_tip_height.set(25)
    await device.scan_direction.set(-1)

    assert await device.timeout.get_value() == 100.
    assert await device.canny_lower.get_value() == 5
    assert await device.canny_upper.get_value() == 10
    assert await device.close_ksize.get_value() == 15
    assert await device.close_iterations.get_value() == 20
    assert await device.min_tip_height.get_value() == 25
    assert await device.scan_direction.get_value() == -1


@pytest.mark.asyncio
async def test_preprocessing_soft_parameter_can_be_changed():
    device = await _get_pin_tip_detection_device()

    my_func_called = False

    def my_preprocessing_func(arr: NDArray) -> NDArray:
        nonlocal my_func_called
        my_func_called = True
        return arr

    await device.preprocess.set(my_preprocessing_func)

    f = (await device.preprocess.read())[""]["value"]

    f(None)

    assert my_func_called


@pytest.mark.parametrize("input_array,height,width,reshaped", [
    (np.zeros(shape=(1, )), 1, 1, np.zeros(shape=(1, 1))),
    (np.zeros(shape=(3, )), 1, 1, np.zeros(shape=(1, 1, 3))),
    (np.zeros(shape=(1920*1080)), 1080, 1920, np.zeros(shape=(1080, 1920))),
    (np.zeros(shape=(1920*1080*3)), 1080, 1920, np.zeros(shape=(1080, 1920, 3))),
])
def test_when_data_supplied_THEN_reshaped_correctly_before_call_to_process_array(input_array: NDArray, height: int, width: int, reshaped: NDArray):
    device = EVENT_LOOP.run_until_complete(_get_pin_tip_detection_device())

    device.array_data._backend._set_value(input_array)  # type: ignore
    set_sim_value(device.oav_height, height)
    set_sim_value(device.oav_width, width)

    MxSampleDetect.processArray = MagicMock(
        autospec=True,
        return_value=SampleLocation(tip_x=10, tip_y=20, edge_bottom=np.array([]), edge_top=np.array([])),
    )

    result = EVENT_LOOP.run_until_complete(device.read())

    MxSampleDetect.processArray.assert_called_once()
    np.testing.assert_array_equal(MxSampleDetect.processArray.call_args[0][0], reshaped)

    assert result[""]["value"] == (10, 20)


@pytest.mark.parametrize("input_array,height,width", [
    (np.zeros(shape=(0,)), 1080, 1920),
    (np.zeros(shape=(1920*1080*2)), 1080, 1920),
])
def test_when_invalid_data_length_supplied_THEN_no_call_to_process_array(input_array: NDArray, height: int, width: int):
    device = EVENT_LOOP.run_until_complete(_get_pin_tip_detection_device())

    set_sim_value(device.array_data, input_array)
    set_sim_value(device.oav_height, height)
    set_sim_value(device.oav_width, width)

    MxSampleDetect.processArray = MagicMock(
        autospec=True,
    )

    result = EVENT_LOOP.run_until_complete(device.read())

    MxSampleDetect.processArray.assert_not_called()

    assert result[""]["value"] == (None, None)
