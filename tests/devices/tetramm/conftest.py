from ophyd_async.core import (
    callback_on_mock_put,
    set_mock_value,
)
from ophyd_async.epics.adcore import ADBaseDataType

from dodal.devices.tetramm.tetramm import (
    TetrammChannels,
    TetrammDetector,
)


def configure_tetramm(tetramm: TetrammDetector):
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

    async def stop_writer_when_triggered(value: bool):
        """The tetramm does not disarm itself after the expected number of triggers,
        instead we rely on the writer having received the correct number of frames.
        Here we use the acquire being set to assume it is immediately triggered.
        """
        set_mock_value(tetramm.file_io.capture, False)

    callback_on_mock_put(tetramm.driver.acquire, stop_writer_when_triggered)
