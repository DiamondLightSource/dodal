import re
from unittest.mock import MagicMock, patch

import pytest
from ophyd_async.core import (
    DetectorTrigger,
    PathProvider,
    TriggerInfo,
    callback_on_mock_put,
    init_devices,
    set_mock_value,
)
from ophyd_async.epics.adcore import ADBaseDataType, ADFileWriteMode

from dodal.devices.tetramm import (
    TetrammChannels,
    TetrammDetector,
    TetrammDriver,
    TetrammTrigger,
)


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
    set_mock_value(tetramm.driver.data_type, ADBaseDataType.FLOAT64)

    async def sample_time_from_values(value: int):
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
        trigger=DetectorTrigger.EXTERNAL_LEVEL,
        deadtime=1e-4,
        livetime=1,
        exposure_timeout=0.001,
    )


VALID_TEST_TOTAL_TRIGGERS = 5
VALID_TEST_EXPOSURE_TIME_PER_COLLECTION = 1 / 6
VALID_TEST_EXPOSURE_TIME = (
    VALID_TEST_EXPOSURE_TIME_PER_COLLECTION / VALID_TEST_TOTAL_TRIGGERS
)
VALID_TEST_DEADTIME = 1 / 100


async def test_set_exposure_updates_values_per_reading(
    tetramm: TetrammDetector,
):
    await tetramm._trigger_logic.set_exposure(VALID_TEST_EXPOSURE_TIME)  # type:ignore
    values_per_reading = await tetramm.driver.values_per_reading.get_value()
    assert values_per_reading == 5


async def test_set_invalid_exposure_for_number_of_values_per_reading(
    tetramm: TetrammDetector,
):
    """Test invalid exposure values.

    Exposure >= minimal_samples * sample_time.
    With the default values::
        minimal_samples = 5.
        sample_time = 100_000.
        exposure >= 5 * 100_000.
    """
    with pytest.raises(
        ValueError,
        match="Tetramm exposure time must be at least 5e-05s, asked to set it to 4e-05s",
    ):
        await tetramm.prepare(
            TriggerInfo(
                number_of_events=0,
                trigger=DetectorTrigger.EXTERNAL_EDGE,
                livetime=4e-5,
            )
        )


@pytest.mark.parametrize(
    "trigger_type",
    [
        DetectorTrigger.INTERNAL,
    ],
)
async def test_arm_raises_value_error_for_invalid_trigger_type(
    tetramm: TetrammDetector,
    trigger_type: DetectorTrigger,
):
    accepted_types = (
        f"[{DetectorTrigger.EXTERNAL_EDGE.name}, {DetectorTrigger.EXTERNAL_LEVEL.name}]"
    )
    with pytest.raises(
        ValueError,
        match=re.escape(
            f"Trigger type {trigger_type} not supported by '{tetramm.name}',"
            f" supported types are: {accepted_types}"
        ),
    ):
        await tetramm.prepare(
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
        DetectorTrigger.EXTERNAL_EDGE,
        DetectorTrigger.EXTERNAL_LEVEL,
    ],
)
async def test_arm_sets_signals_correctly_given_valid_inputs(
    tetramm: TetrammDetector,
    trigger_type: DetectorTrigger,
):
    trigger_info = TriggerInfo(
        number_of_events=0,
        trigger=trigger_type,
        livetime=VALID_TEST_EXPOSURE_TIME,
        deadtime=VALID_TEST_DEADTIME,
    )
    await tetramm.prepare(trigger_info)

    await assert_armed(tetramm.driver, trigger_info)


async def test_disarm_disarms_driver(
    tetramm: TetrammDetector,
):
    assert (await tetramm.driver.acquire.get_value()) == 0
    await tetramm.prepare(
        TriggerInfo(
            number_of_events=0,
            trigger=DetectorTrigger.EXTERNAL_EDGE,
            livetime=VALID_TEST_EXPOSURE_TIME,
            deadtime=VALID_TEST_DEADTIME,
        )
    )
    assert (await tetramm.driver.acquire.get_value()) == 1
    await tetramm._arm_logic.disarm()  # type: ignore
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
                trigger=DetectorTrigger.EXTERNAL_EDGE,
                deadtime=1.0 / 100_000.0,
                livetime=VALID_TEST_EXPOSURE_TIME,
            )
        )


async def test_prepare_arms_tetramm(tetramm: TetrammDetector):
    trigger_info = TriggerInfo(
        number_of_events=5,
        trigger=DetectorTrigger.EXTERNAL_EDGE,
        deadtime=0.1,
        livetime=VALID_TEST_EXPOSURE_TIME,
    )

    await tetramm.prepare(trigger_info)
    await assert_armed(tetramm.driver, trigger_info)


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
    tetramm: TetrammDetector,
    static_path_provider: PathProvider,  # , supported_trigger_info: TriggerInfo
):

    trigger_info = TriggerInfo(
        number_of_events=1,
        trigger=DetectorTrigger.EXTERNAL_EDGE,
        deadtime=1e-4,
        livetime=1,
        exposure_timeout=0.001,
    )

    # assert await tetramm.describe() == {}
    await tetramm.stage()
    await tetramm.prepare(trigger_info)

    averaging_time = await tetramm.driver.averaging_time.get_value()
    averaging_time = round(averaging_time, 3)  # avoid floating point issues

    assert averaging_time == 1.0

    path_info = static_path_provider(tetramm.name)
    expected_path = (
        path_info.directory_path.joinpath(path_info.filename + ".h5")
        .as_uri()
        .replace("file:///", "file://localhost/")
    )

    assert await tetramm.describe() == {
        "tetramm": {
            "source": expected_path,
            "shape": [1, 4, averaging_time],
            "dtype_numpy": "<f8",
            "dtype": "array",
            "external": "STREAM:",
        }
    }


async def test_error_if_armed_without_exposure(
    tetramm: TetrammDetector,
):
    with pytest.raises(ValueError):
        await tetramm.prepare(
            TriggerInfo(number_of_events=10, trigger=DetectorTrigger.EXTERNAL_LEVEL)
        )


async def test_tetramm_controller(
    tetramm: TetrammDetector,
):
    await tetramm.prepare(
        TriggerInfo(
            number_of_events=1,
            trigger=DetectorTrigger.EXTERNAL_LEVEL,
            livetime=VALID_TEST_EXPOSURE_TIME,
            deadtime=VALID_TEST_DEADTIME,
        )
    )
    await tetramm._arm_logic.arm()  # type: ignore
    await tetramm._arm_logic.wait_for_idle()  # type:ignore

    assert await tetramm.driver.acquire.get_value() is True

    await tetramm._arm_logic.disarm()  # type: ignore

    assert await tetramm.driver.acquire.get_value() is False


async def test_tetramm_unstage(tetramm: TetrammDetector):
    data_logic = tetramm._data_logics[0]

    with patch.object(data_logic, "stop") as mock_stop:
        await tetramm.unstage()
        mock_stop.assert_called_once()


async def test_tetramm_prepare_when_freerunning(
    tetramm: TetrammDetector,
):
    set_mock_value(tetramm.driver.trigger_mode, TetrammTrigger.FREE_RUN)
    set_mock_value(tetramm.driver.acquire, True)

    with patch.object(tetramm._arm_logic, "disarm") as mock_disarm:
        await tetramm.prepare(
            TriggerInfo(
                number_of_events=1,
                trigger=DetectorTrigger.EXTERNAL_LEVEL,
                livetime=VALID_TEST_EXPOSURE_TIME,
                deadtime=VALID_TEST_DEADTIME,
            )
        )
        mock_disarm.assert_called_once()


async def assert_armed(driver: TetrammDriver, trigger_info: TriggerInfo) -> None:
    sample_time = await driver.sample_time.get_value()
    samples_per_reading = int(VALID_TEST_EXPOSURE_TIME / sample_time)
    averaging_time = samples_per_reading * sample_time

    assert (await driver.trigger_mode.get_value()) is TetrammTrigger.EXT_TRIGGER
    assert (await driver.values_per_reading.get_value()) == 5
    assert (await driver.acquire.get_value()) == 1

    # Live time not used for EXTERNAL_LEVEL
    if trigger_info.trigger is not DetectorTrigger.EXTERNAL_LEVEL:
        assert (await driver.averaging_time.get_value()) == averaging_time


@patch("ophyd_async.epics.adcore._arm_logic.stop_busy_record")
async def test_tetramm_disarm_calls_stop_busy_recording(
    stop_busy_record_mock: MagicMock,
    tetramm: TetrammDetector,
):
    await tetramm._arm_logic.disarm()  # type: ignore
    stop_busy_record_mock.assert_called_once()
