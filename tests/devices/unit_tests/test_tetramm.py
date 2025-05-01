import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import DetectorTrigger, PathProvider, TriggerInfo, init_devices
from ophyd_async.epics.adcore import ADFileWriteMode
from ophyd_async.testing import set_mock_value

from dodal.devices.tetramm import (
    TetrammController,
    TetrammDetector,
    TetrammDriver,
    TetrammTrigger,
)

TEST_TETRAMM_NAME = "foobar"


@pytest.fixture
async def tetramm_driver(RE: RunEngine) -> TetrammDriver:
    async with init_devices(mock=True):
        driver = TetrammDriver("DRIVER:")

    return driver


@pytest.fixture
async def tetramm_controller(
    RE: RunEngine, tetramm_driver: TetrammDriver
) -> TetrammController:
    async with init_devices(mock=True):
        controller = TetrammController(
            tetramm_driver,
            maximum_readings_per_frame=2_000,
        )

    return controller


@pytest.fixture
async def tetramm(static_path_provider: PathProvider) -> TetrammDetector:
    async with init_devices(mock=True):
        tetramm = TetrammDetector(
            "MY-TETRAMM:",
            static_path_provider,
            name=TEST_TETRAMM_NAME,
        )
    set_mock_value(tetramm.hdf.file_path_exists, True)

    return tetramm


@pytest.fixture
def supported_trigger_info() -> TriggerInfo:
    return TriggerInfo(
        number_of_events=1,
        trigger=DetectorTrigger.CONSTANT_GATE,
        deadtime=1.0,
        livetime=0.02,
        exposure_timeout=None,
    )


async def test_max_frame_rate_is_calculated_correctly(
    tetramm_controller: TetrammController,
):
    await tetramm_controller.prepare(
        TriggerInfo(
            number_of_events=1, trigger=DetectorTrigger.EDGE_TRIGGER, livetime=2.0
        )
    )

    assert tetramm_controller.minimum_exposure == 0.1
    assert tetramm_controller.max_frame_rate == 10.0

    # Ensure that the minimum frame time is correctly calculated given a maximum
    # frame rate.
    # max_frame_rate**-1 = minimum_exposures
    tetramm_controller.max_frame_rate = 20.0
    assert tetramm_controller.minimum_exposure == pytest.approx(1 / 20)


async def test_min_exposure_is_calculated_correctly(
    tetramm_controller: TetrammController,
):
    # Using coprimes to ensure the solution has a unique relation to the values.
    tetramm_controller.base_sample_rate = 100_000
    tetramm_controller.readings_per_frame = 999
    tetramm_controller.maximum_readings_per_frame = 1_001
    tetramm_controller.minimum_values_per_reading = 17

    # min_exposure (s/f) = max_readings_per_frame * values_per_reading / sample_rate (v/s)
    minimum_exposure = (
        tetramm_controller.readings_per_frame
        * tetramm_controller.minimum_values_per_reading
        / float(tetramm_controller.base_sample_rate)
    )

    assert tetramm_controller.minimum_exposure == pytest.approx(minimum_exposure)

    # From rearranging the above
    # readings_per_frame = exposure * sample_rate / values_per_reading

    readings_per_time = (
        tetramm_controller.base_sample_rate
        / tetramm_controller.minimum_values_per_reading
    )

    # 100_000 / 17 ~ 5800; 5800 * 0.01 = 58; 58 << tetramm_controller.maximum_readings_per_frame
    await tetramm_controller.prepare(
        TriggerInfo(
            number_of_events=1, trigger=DetectorTrigger.EDGE_TRIGGER, livetime=0.01
        )
    )
    assert tetramm_controller.readings_per_frame == int(readings_per_time * 0.01)

    # 100_000 / 17 ~ 5800; 5800 * 0.2 = 1160; 1160 > tetramm_controller.maximum_readings_per_frame
    await tetramm_controller.prepare(
        TriggerInfo(
            number_of_events=1, trigger=DetectorTrigger.EDGE_TRIGGER, livetime=0.2
        )
    )
    assert (
        tetramm_controller.readings_per_frame
        == tetramm_controller.maximum_readings_per_frame
    )

    # 100_000 / 17 ~ 5800; 5800 * 0.2 = 1160; 1160 < 1200
    tetramm_controller.maximum_readings_per_frame = 1200
    await tetramm_controller.prepare(
        TriggerInfo(
            number_of_events=1, trigger=DetectorTrigger.EDGE_TRIGGER, livetime=0.1
        )
    )
    assert tetramm_controller.readings_per_frame == int(readings_per_time * 0.1)


VALID_TEST_EXPOSURE_TIME = 1 / 19
VALID_TEST_DEADTIME = 1 / 100


async def test_set_exposure_updates_values_per_reading(
    tetramm_controller: TetrammController,
    tetramm_driver: TetrammDriver,
):
    await tetramm_controller.set_exposure(VALID_TEST_EXPOSURE_TIME)
    values_per_reading = await tetramm_driver.values_per_reading.get_value()
    assert values_per_reading == 5


async def test_set_invalid_exposure_for_number_of_values_per_reading(
    tetramm_controller: TetrammController,
):
    """
    exposure >= readings_per_frame * values_per_reading / sample_rate
    With the default values:
    base_sample_rate = 100_000
    minimum_values_per_reading = 5
    readings_per_frame = 5
    exposure >= 5 * 5 / 100_000 = 1/4000
    """

    with pytest.raises(
        ValueError,
        match="Tetramm exposure time must be at least 5e-05s, asked to set it to 4e-05s",
    ):
        await tetramm_controller.prepare(
            TriggerInfo(
                number_of_events=0,
                trigger=DetectorTrigger.EDGE_TRIGGER,
                livetime=4e-5,
            )
        )


@pytest.mark.parametrize(
    "exposure,expected_values_per_reading",
    [
        (20.0, 2000),
        (10.0, 1000),
        (1.0, 100),
        (0.1, 10),
        (0.05, 5),  # Smallest exposure time where we can still have 1000 readings per
        # frame
        (1 / 50.0, 5),
        (1 / 1000.0, 5),
        (5e-5, 5),  # Smallest possible exposure time
    ],
)
async def test_sample_rate_scales_with_exposure_time(
    tetramm: TetrammDetector,
    exposure: float,
    expected_values_per_reading: int,
):
    set_mock_value(tetramm.hdf.file_path_exists, True)

    await tetramm.prepare(
        TriggerInfo(
            number_of_events=100,
            trigger=DetectorTrigger.EDGE_TRIGGER,
            deadtime=2e-5,
            livetime=exposure,
            exposure_timeout=None,
        )
    )
    values_per_reading = await tetramm.drv.values_per_reading.get_value()
    assert values_per_reading == expected_values_per_reading


@pytest.mark.parametrize(
    "trigger_type",
    [
        DetectorTrigger.INTERNAL,
        DetectorTrigger.VARIABLE_GATE,
    ],
)
async def test_arm_raises_value_error_for_invalid_trigger_type(
    tetramm_controller: TetrammController,
    trigger_type: DetectorTrigger,
):
    accepted_types = {
        DetectorTrigger.EDGE_TRIGGER,
        DetectorTrigger.CONSTANT_GATE,
    }
    with pytest.raises(
        ValueError,
        match="TetrammController only supports the following trigger "
        f"types: {accepted_types} but was asked to "
        f"use {trigger_type}",
    ):
        await tetramm_controller.prepare(
            TriggerInfo(
                number_of_events=0,
                trigger=trigger_type,
                livetime=VALID_TEST_EXPOSURE_TIME,
                deadtime=VALID_TEST_DEADTIME,
            )
        )


@pytest.mark.parametrize(
    "trigger_type",
    [
        DetectorTrigger.EDGE_TRIGGER,
        DetectorTrigger.CONSTANT_GATE,
    ],
)
async def test_arm_sets_signals_correctly_given_valid_inputs(
    tetramm: TetrammDetector,
    trigger_type: DetectorTrigger,
):
    await tetramm.prepare(
        TriggerInfo(
            number_of_events=0,
            trigger=trigger_type,
            livetime=VALID_TEST_EXPOSURE_TIME,
            deadtime=VALID_TEST_DEADTIME,
        )
    )

    await assert_armed(tetramm.drv)


async def test_disarm_disarms_driver(
    tetramm: TetrammDetector,
):
    tetramm_driver = tetramm.drv
    assert (await tetramm_driver.acquire.get_value()) == 0
    await tetramm.prepare(
        TriggerInfo(
            number_of_events=0,
            trigger=DetectorTrigger.EDGE_TRIGGER,
            livetime=VALID_TEST_EXPOSURE_TIME,
            deadtime=VALID_TEST_DEADTIME,
        )
    )
    assert (await tetramm_driver.acquire.get_value()) == 1
    await tetramm._controller.disarm()
    assert (await tetramm_driver.acquire.get_value()) == 0


async def test_hints_self_by_default(tetramm: TetrammDetector):
    assert tetramm.hints == {"fields": [TEST_TETRAMM_NAME]}


async def test_prepare_with_too_low_a_deadtime_raises_error(
    tetramm: TetrammDetector,
):
    with pytest.raises(
        ValueError,
        match=r"Detector .* needs at least 2e-05s deadtime, but trigger logic "
        "provides only 1e-05s",
    ):
        await tetramm.prepare(
            TriggerInfo(
                number_of_events=5,
                trigger=DetectorTrigger.EDGE_TRIGGER,
                deadtime=1.0 / 100_000.0,
                livetime=VALID_TEST_EXPOSURE_TIME,
                exposure_timeout=None,
            )
        )


async def test_prepare_arms_tetramm(
    tetramm: TetrammDetector,
):
    set_mock_value(tetramm.hdf.file_path_exists, True)
    await tetramm.prepare(
        TriggerInfo(
            number_of_events=5,
            trigger=DetectorTrigger.EDGE_TRIGGER,
            deadtime=0.1,
            livetime=VALID_TEST_EXPOSURE_TIME,
            exposure_timeout=None,
        )
    )
    await assert_armed(tetramm.drv)


async def test_prepare_sets_up_writer(
    tetramm: TetrammDetector, supported_trigger_info: TriggerInfo
):
    set_mock_value(tetramm.hdf.file_path_exists, True)
    await tetramm.stage()
    await tetramm.prepare(supported_trigger_info)

    assert (await tetramm.hdf.num_capture.get_value()) == 0
    assert (await tetramm.hdf.num_extra_dims.get_value()) == 0
    assert await tetramm.hdf.lazy_open.get_value()
    assert await tetramm.hdf.swmr_mode.get_value()
    assert (await tetramm.hdf.file_template.get_value()) == "%s%s.h5"
    assert (await tetramm.hdf.file_write_mode.get_value()) == ADFileWriteMode.STREAM


async def test_stage_sets_up_accurate_describe_output(
    tetramm: TetrammDetector, supported_trigger_info: TriggerInfo
):
    assert await tetramm.describe() == {}

    set_mock_value(tetramm.hdf.file_path_exists, True)
    await tetramm.stage()
    await tetramm.prepare(supported_trigger_info)

    assert await tetramm.describe() == {
        TEST_TETRAMM_NAME: {
            "source": "mock+ca://MY-TETRAMM:HDF5:FullFileName_RBV",
            "shape": [1, 11, 400],
            "dtype_numpy": "<f8",
            "dtype": "array",
            "external": "STREAM:",
        }
    }


async def test_error_if_armed_without_exposure(tetramm_controller: TetrammController):
    with pytest.raises(ValueError):
        await tetramm_controller.prepare(
            TriggerInfo(number_of_events=10, trigger=DetectorTrigger.INTERNAL)
        )


async def test_pilatus_controller(
    RE,
    tetramm: TetrammDetector,
):
    controller = tetramm._controller
    driver = tetramm.drv
    await controller.prepare(
        TriggerInfo(
            number_of_events=1,
            trigger=DetectorTrigger.CONSTANT_GATE,
            livetime=VALID_TEST_EXPOSURE_TIME,
            deadtime=VALID_TEST_DEADTIME,
        )
    )
    await controller.arm()
    await controller.wait_for_idle()

    assert await driver.acquire.get_value() is True

    await controller.disarm()

    assert await driver.acquire.get_value() is False


async def assert_armed(driver: TetrammDriver) -> None:
    assert (await driver.trigger_mode.get_value()) is TetrammTrigger.EXT_TRIGGER
    assert (await driver.averaging_time.get_value()) == VALID_TEST_EXPOSURE_TIME
    assert (await driver.values_per_reading.get_value()) == 5
    assert (await driver.acquire.get_value()) == 1
