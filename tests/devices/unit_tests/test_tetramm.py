from unittest.mock import Mock

import pytest
from ophyd_async.core import DetectorTrigger, DeviceCollector

from dodal.devices.tetramm import (
    TetrammController,
    TetrammDetector,
    TetrammDriver,
    TetrammTrigger,
)

TEST_TETRAMM_NAME = "foobar"


@pytest.fixture
async def tetramm_driver(RE) -> TetrammDriver:
    async with DeviceCollector(sim=True):
        driver = TetrammDriver("DRIVER:")

    return driver


@pytest.fixture
async def tetramm_controller(RE, tetramm_driver: TetrammDriver) -> TetrammController:
    async with DeviceCollector(sim=True):
        controller = TetrammController(
            tetramm_driver,
            maximum_readings_per_frame=2_000,
        )

    return controller


@pytest.fixture
async def tetramm() -> TetrammDetector:
    async with DeviceCollector(sim=True):
        tetramm = TetrammDetector(
            "MY-TETRAMM:",
            Mock(),
            name=TEST_TETRAMM_NAME,
        )

    return tetramm


from ophyd_async.core import set_sim_value


async def test_max_frame_rate_is_calculated_correctly(
    tetramm_controller: TetrammController,
):
    tetramm_controller.minimum_frame_time = 2.0

    assert tetramm_controller.minimum_frame_time == 0.1
    assert tetramm_controller.max_frame_rate == 10.0

    # Ensure that the minimum frame time is correctly calculated given a maximum
    # frame rate.
    # max_frame_rate**-1 = minimum_frame_times
    tetramm_controller.max_frame_rate = 20.0
    assert tetramm_controller.minimum_frame_time == pytest.approx(1 / 20)


def test_min_frame_time_is_calculated_correctly(
    tetramm_controller: TetrammController,
):
    tetramm_controller = tetramm_controller
    # Using coprimes to ensure the solution has a unique relation to the values.
    tetramm_controller.base_sample_rate = 100_000
    tetramm_controller.readings_per_frame = 999
    tetramm_controller.maximum_readings_per_frame = 1_001
    tetramm_controller.minimum_values_per_reading = 17

    # min_frame_time (s/f) = max_readings_per_frame * values_per_reading / sample_rate (v/s)
    minimum_frame_time = (
        tetramm_controller.readings_per_frame
        * tetramm_controller.minimum_values_per_reading
        / float(tetramm_controller.base_sample_rate)
    )

    assert tetramm_controller.minimum_frame_time == pytest.approx(minimum_frame_time)

    # From rearranging the above
    # readings_per_frame = frame_time * sample_rate / values_per_reading

    readings_per_time = (
        tetramm_controller.base_sample_rate
        / tetramm_controller.minimum_values_per_reading
    )

    # 100_000 / 17 ~ 5800; 5800 * 0.01 = 58; 58 << tetramm_controller.maximum_readings_per_frame
    tetramm_controller.minimum_frame_time = 0.01
    assert tetramm_controller.readings_per_frame == int(readings_per_time * 0.01)

    # 100_000 / 17 ~ 5800; 5800 * 0.2 = 1160; 1160 > tetramm_controller.maximum_readings_per_frame
    tetramm_controller.minimum_frame_time = 0.2
    assert (
        tetramm_controller.readings_per_frame
        == tetramm_controller.maximum_readings_per_frame
    )

    # 100_000 / 17 ~ 5800; 5800 * 0.2 = 1160; 1160 < 1200
    tetramm_controller.maximum_readings_per_frame = 1200
    tetramm_controller.minimum_frame_time = 0.1
    assert tetramm_controller.readings_per_frame == int(readings_per_time * 0.1)


VALID_TEST_EXPOSURE_TIME = 1 / 19


async def test_set_frame_time_updates_values_per_reading(
    tetramm_controller: TetrammController,
    tetramm_driver: TetrammDriver,
):
    await tetramm_controller.set_frame_time(VALID_TEST_EXPOSURE_TIME)
    values_per_reading = await tetramm_driver.values_per_reading.get_value()
    assert values_per_reading == 5


async def test_set_invalid_frame_time_for_number_of_values_per_reading(
    tetramm_controller: TetrammController,
):
    """
    frame_time >= readings_per_frame * values_per_reading / sample_rate
    With the default values:
    base_sample_rate = 100_000
    minimum_values_per_reading = 5
    readings_per_frame = 1_000
    frame_time >= 1_000 * 5 / 100_000 = 1/20
    """

    with pytest.raises(
        ValueError,
        match="frame_time 0.02 is too low to collect at least 5 values per reading, at 1000 readings per frame.",
    ):
        await (await tetramm_controller.arm(-1, DetectorTrigger.edge_trigger, 1 / 50))


@pytest.mark.parametrize(
    "trigger_type",
    [
        DetectorTrigger.internal,
        DetectorTrigger.variable_gate,
    ],
)
async def test_arm_raises_value_error_for_invalid_trigger_type(
    tetramm_controller: TetrammController,
    trigger_type: DetectorTrigger,
):
    with pytest.raises(ValueError):
        await tetramm_controller.arm(
            -1,
            trigger_type,
            VALID_TEST_EXPOSURE_TIME,
        )


@pytest.mark.parametrize(
    "trigger_type",
    [
        DetectorTrigger.edge_trigger,
        DetectorTrigger.constant_gate,
    ],
)
async def test_arm_sets_signals_correctly_given_valid_inputs(
    tetramm_controller: TetrammController,
    tetramm_driver: TetrammDriver,
    trigger_type: DetectorTrigger,
):
    arm_status = await tetramm_controller.arm(
        -1, trigger_type, VALID_TEST_EXPOSURE_TIME
    )
    await arm_status

    assert (await tetramm_driver.trigger_mode.get_value()) is TetrammTrigger.ExtTrigger
    assert (await tetramm_driver.averaging_time.get_value()) == VALID_TEST_EXPOSURE_TIME
    assert (await tetramm_driver.values_per_reading.get_value()) == 5
    assert (await tetramm_driver.acquire.get_value()) == 1


async def test_disarm_disarms_driver(
    tetramm_controller: TetrammController,
    tetramm_driver: TetrammDriver,
):
    assert (await tetramm_driver.acquire.get_value()) == 0
    arm_status = await tetramm_controller.arm(
        -1, DetectorTrigger.edge_trigger, VALID_TEST_EXPOSURE_TIME
    )
    await arm_status
    assert (await tetramm_driver.acquire.get_value()) == 1
    await tetramm_controller.disarm()
    assert (await tetramm_driver.acquire.get_value()) == 0


async def test_hints_self_by_default(tetramm: TetrammDetector):
    assert tetramm.hints == {"fields": [TEST_TETRAMM_NAME]}
