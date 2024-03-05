from unittest.mock import Mock

import pytest
from ophyd_async.core import DetectorTrigger, DeviceCollector

from dodal.devices.tetramm import TetrammController, TetrammDriver


@pytest.fixture
async def tetramm_controller(RE) -> TetrammController:
    async with DeviceCollector(sim=True):
        drv = TetrammDriver("DRIVER:")
        controller = TetrammController(drv)

    return controller


def test_max_frame_rate():
    drv = Mock()
    drv.minimum_frame_time = 0.1
    assert TetrammController.max_frame_rate.__get__(drv) == 10
    TetrammController.max_frame_rate.__set__(drv, 20)
    # max_frame_rate**-1 = minimum_frame_times
    assert drv.minimum_frame_time == pytest.approx(1 / 20)


def test_min_frame_time():
    drv = Mock()
    # Using coprimes to ensure the solution has a unique relation to the values.
    drv.base_sample_rate = 100_000
    drv.readings_per_frame = 999
    drv.maximum_readings_per_frame = 1_001
    drv.minimum_values_per_reading = 17

    # min_frame_time (s/f) = max_readings_per_frame * values_per_reading / sample_rate (v/s)
    minimum_frame_time = (
        drv.readings_per_frame
        * drv.minimum_values_per_reading
        / float(drv.base_sample_rate)
    )

    assert TetrammController.minimum_frame_time.__get__(drv) == pytest.approx(
        minimum_frame_time
    )

    # From rearranging the above
    # readings_per_frame = frame_time * sample_rate / values_per_reading

    readings_per_time = drv.base_sample_rate / drv.minimum_values_per_reading

    # 100_000 / 17 ~ 5800; 5800 * 0.01 = 58; 58 << drv.maximum_readings_per_frame
    TetrammController.minimum_frame_time.__set__(drv, 0.01)
    assert drv.readings_per_frame == int(readings_per_time * 0.01)

    # 100_000 / 17 ~ 5800; 5800 * 0.2 = 1160; 1160 > drv.maximum_readings_per_frame
    TetrammController.minimum_frame_time.__set__(drv, 0.2)
    assert drv.readings_per_frame == drv.maximum_readings_per_frame

    # 100_000 / 17 ~ 5800; 5800 * 0.2 = 1160; 1160 < 1200
    drv.maximum_readings_per_frame = 1200
    TetrammController.minimum_frame_time.__set__(drv, 0.1)
    assert drv.readings_per_frame == int(readings_per_time * 0.1)


async def test_excepts_for_invalid_triggers(tetramm_controller: TetrammController):
    previous_averaging_time = tetramm_controller._drv.averaging_time
    with pytest.raises(ValueError):
        await tetramm_controller.arm(DetectorTrigger.internal)
    # Function excepts early and does not do any sets
    assert tetramm_controller._drv.averaging_time == previous_averaging_time
