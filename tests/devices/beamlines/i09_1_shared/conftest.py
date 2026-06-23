import pytest
from daq_config_server import ConfigClient
from daq_config_server.models.lookup_tables.insertion_device import (
    parse_i09_hu_undulator_energy_gap_lut,
)

from dodal.testing.fixtures.config_client import (
    MOCK_CONFIG_CLIENT_PATH_TO_MODEL_CONVERSION,
)
from tests.devices.beamlines.i09_1_shared.test_data import TEST_HARD_UNDULATOR_LUT


@pytest.fixture
def mock_config_client(mock_config_client: ConfigClient):
    MOCK_CONFIG_CLIENT_PATH_TO_MODEL_CONVERSION[TEST_HARD_UNDULATOR_LUT] = (
        parse_i09_hu_undulator_energy_gap_lut
    )
    yield mock_config_client
    MOCK_CONFIG_CLIENT_PATH_TO_MODEL_CONVERSION.pop(TEST_HARD_UNDULATOR_LUT, None)
