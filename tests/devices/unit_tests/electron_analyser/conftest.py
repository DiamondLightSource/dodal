import os

import pytest
from ophyd_async.core import init_devices
from tests.devices.unit_tests.electron_analyser.test_utils import TEST_DATA_PATH

from dodal.common.data_util import TBaseModel, load_json_file_to_class
from dodal.devices.electron_analyser.abstract_analyser import TAbstractBaseAnalyser


@pytest.fixture
def sequence_file_path(sequence_file: str) -> str:
    return os.path.join(TEST_DATA_PATH, sequence_file)


@pytest.fixture
def sequence(sequence_class: type[TBaseModel], sequence_file_path: str) -> TBaseModel:
    return load_json_file_to_class(sequence_class, sequence_file_path)


@pytest.fixture
async def sim_analyser(
    analyser_type: type[TAbstractBaseAnalyser],
) -> TAbstractBaseAnalyser:
    async with init_devices(mock=True):
        sim_analyser = analyser_type(
            prefix="sim_analyser",
            name="analyser",
        )
    return sim_analyser
