import os

import pytest
from ophyd_async.core import init_devices

from dodal.common.data_util import load_json_file_to_class
from dodal.devices.electron_analyser.abstract_analyser_controller import (
    TAbstractAnalyserController,
)
from dodal.devices.electron_analyser.abstract_region import TAbstractBaseSequence

TEST_DATA_PATH = "tests/test_data/electron_analyser/"


@pytest.fixture
def sequence_file_path(sequence_file: str) -> str:
    return os.path.join(TEST_DATA_PATH, sequence_file)


@pytest.fixture
def sequence(
    sequence_class: type[TAbstractBaseSequence], sequence_file_path: str
) -> TAbstractBaseSequence:
    return load_json_file_to_class(sequence_class, sequence_file_path)


@pytest.fixture
async def sim_analyser(
    analyser_type: type[TAbstractAnalyserController],
) -> TAbstractAnalyserController:
    async with init_devices(mock=True):
        sim_analyser = analyser_type(
            prefix="sim_analyser",
            name="analyser",
        )
    return sim_analyser
