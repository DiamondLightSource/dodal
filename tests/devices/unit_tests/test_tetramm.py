from dodal.devices.tetramm import TetrammDriver
from unittest.mock import Mock

TOLERANCE = 0.0001

def test_max_frame_rate():
    drv = Mock()
    drv.minimum_frame_time = 0.1
    assert TetrammDriver.max_frame_rate.__get__(drv) == 10
    TetrammDriver.max_frame_rate.__set__(drv, 20)
    assert abs(drv.minimum_frame_time - 0.05) < TOLERANCE

def test_min_frame_time():
    drv = Mock()
    drv.base_sample_rate = 100_000
    drv.maximum_readings_per_frame = 1_000
    drv.minimum_values_per_reading = 5
    drv.readings_per_frame = 1_000

    assert abs(TetrammDriver.minimum_frame_time.__get__(drv) - 0.05) < TOLERANCE

    TetrammDriver.minimum_frame_time.__set__(drv, 0.01)
    assert drv.readings_per_frame == 200

    # readings_per_frame should never be above maximum_readings_per_frame
    TetrammDriver.minimum_frame_time.__set__(drv, 0.1)
    assert drv.readings_per_frame == 1000

    drv.maximum_readings_per_frame = 1200
    TetrammDriver.minimum_frame_time.__set__(drv, 0.1)
    assert drv.readings_per_frame == 1200
