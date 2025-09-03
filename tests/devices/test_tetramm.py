import re

import pytest
from ophyd_async.core import DetectorTrigger, PathProvider, TriggerInfo, init_devices
from ophyd_async.epics.adcore import ADFileWriteMode
from ophyd_async.testing import callback_on_mock_put, set_mock_value

from dodal.devices.tetramm import (
    TetrammChannels,
    TetrammController,
    TetrammDetector,
    TetrammDriver,
    TetrammTrigger,
)


@pytest.fixture
async def tetramm_controller(tetramm: TetrammDetector) -> TetrammController:
    return tetramm._controller


@pytest.fixture
async def tetramm(static_path_provider: PathProvider) -> TetrammDetector:
    async with init_devices(mock=True):
        tetramm = TetrammDetector(
            "MY-TETRAMM:",
            static_path_provider,
        )
    set_mock_value(tetramm.file_io.file_path_exists, True)
    set_mock_value(tetramm.driver.to_average, 1)
    set_mock_value(tetramm.driver.averaged, 1)
    set_mock_value(tetramm.driver.num_channels, TetrammChannels.FOUR)
    set_mock_value(tetramm.driver.sample_time, 10e-6)

    async def sample_time_from_values(value: int, _: bool):
        # https://millenia.cars.aps.anl.gov/software/epics/quadEMDoc.html
        # "The sample time on the TetrAMM is controlled by the following equation:
        # 10 microseconds * ValuesPerRead.""
        set_mock_value(tetramm.driver.sample_time, 10e-6 * value)

    callback_on_mock_put(tetramm.driver.values_per_reading, sample_time_from_values)
    set_mock_value(tetramm.driver.values_per_reading, 5)
    set_mock_value(tetramm.driver.averaging_time, 10e-6)

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


VALID_TEST_EXPOSURE_TIME = 1 / 19
VALID_TEST_DEADTIME = 1 / 100


async def test_set_exposure_updates_values_per_reading(
    tetramm_controller: TetrammController,
    tetramm: TetrammDetector,
):
    await tetramm_controller.set_exposure(VALID_TEST_EXPOSURE_TIME)
    values_per_reading = await tetramm.driver.values_per_reading.get_value()
    assert values_per_reading == 5


async def test_set_invalid_exposure_for_number_of_values_per_reading(
    tetramm_controller: TetrammController,
):
    """
    exposure >= minimal_samples * sample_time
    With the default values:
    minimal_samples = 5
    sample_time = 100_000
    exposure >= 5 * 100_000
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
    accepted_types = [
        "EDGE_TRIGGER",
        "CONSTANT_GATE",
    ]
    with pytest.raises(
        TypeError,
        match=re.escape(
            "TetrammController only supports the following trigger "
            f"types: {accepted_types} but was asked to "
            f"use {trigger_type}"
        ),
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

    await assert_armed(tetramm.driver)


async def test_disarm_disarms_driver(
    tetramm: TetrammDetector,
):
    assert (await tetramm.driver.acquire.get_value()) == 0
    await tetramm.prepare(
        TriggerInfo(
            number_of_events=0,
            trigger=DetectorTrigger.EDGE_TRIGGER,
            livetime=VALID_TEST_EXPOSURE_TIME,
            deadtime=VALID_TEST_DEADTIME,
        )
    )
    assert (await tetramm.driver.acquire.get_value()) == 1
    await tetramm._controller.disarm()
    assert (await tetramm.driver.acquire.get_value()) == 0


async def test_hints_self_by_default(tetramm: TetrammDetector):
    assert tetramm.hints == {"fields": [tetramm.name]}


async def test_prepare_with_too_low_a_deadtime_raises_error(
    tetramm: TetrammDetector,
):
    with pytest.raises(
        ValueError,
        match=r"Tetramm .* needs at least 2e-05s deadtime, but trigger logic "
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
    await tetramm.prepare(
        TriggerInfo(
            number_of_events=5,
            trigger=DetectorTrigger.EDGE_TRIGGER,
            deadtime=0.1,
            livetime=VALID_TEST_EXPOSURE_TIME,
            exposure_timeout=None,
        )
    )
    await assert_armed(tetramm.driver)


async def test_prepare_sets_up_writer(
    tetramm: TetrammDetector, supported_trigger_info: TriggerInfo
):
    await tetramm.stage()
    await tetramm.prepare(supported_trigger_info)

    assert (await tetramm.file_io.num_capture.get_value()) == 0
    assert (await tetramm.file_io.num_extra_dims.get_value()) == 0
    assert (await tetramm.file_io.lazy_open.get_value()) is True
    assert (await tetramm.file_io.swmr_mode.get_value()) is True
    assert (await tetramm.file_io.file_template.get_value()) == "%s%s.h5"
    assert (await tetramm.file_io.file_write_mode.get_value()) == ADFileWriteMode.STREAM


async def test_stage_sets_up_accurate_describe_output(
    tetramm: TetrammDetector, supported_trigger_info: TriggerInfo
):
    assert await tetramm.describe() == {}
    await tetramm.stage()
    await tetramm.prepare(supported_trigger_info)

    assert await tetramm.describe() == {
        "tetramm": {
            "source": "mock+ca://MY-TETRAMM:HDF5:FullFileName_RBV",
            "shape": [1, 4, 1999],
            "dtype_numpy": "<f8",
            "dtype": "array",
            "external": "STREAM:",
        }
    }


async def test_error_if_armed_without_exposure(tetramm_controller: TetrammController):
    with pytest.raises(ValueError):
        await tetramm_controller.prepare(
            TriggerInfo(number_of_events=10, trigger=DetectorTrigger.CONSTANT_GATE)
        )


async def test_pilatus_controller(
    tetramm: TetrammDetector,
    tetramm_controller: TetrammController,
):
    await tetramm_controller.prepare(
        TriggerInfo(
            number_of_events=1,
            trigger=DetectorTrigger.CONSTANT_GATE,
            livetime=VALID_TEST_EXPOSURE_TIME,
            deadtime=VALID_TEST_DEADTIME,
        )
    )
    await tetramm_controller.arm()
    await tetramm_controller.wait_for_idle()

    assert await tetramm.driver.acquire.get_value() is True

    await tetramm_controller.disarm()

    assert await tetramm.driver.acquire.get_value() is False


async def assert_armed(driver: TetrammDriver) -> None:
    sample_time = await driver.sample_time.get_value()
    samples_per_reading = int(VALID_TEST_EXPOSURE_TIME / sample_time)
    exposure = samples_per_reading * sample_time

    assert (await driver.trigger_mode.get_value()) is TetrammTrigger.EXT_TRIGGER
    assert (await driver.averaging_time.get_value()) == exposure
    assert (await driver.values_per_reading.get_value()) == 5
    assert (await driver.acquire.get_value()) == 1
