import pytest
from daq_config_server import ConfigClient
from daq_config_server.models.lookup_tables.insertion_device import (
    parse_i09_hu_undulator_energy_gap_lut,
)

from tests.devices.beamlines.i09_1_shared.test_data import TEST_HARD_UNDULATOR_LUT


@pytest.fixture
def mock_config_client(mock_config_client_with_data) -> ConfigClient:
    return mock_config_client_with_data(
        {TEST_HARD_UNDULATOR_LUT: parse_i09_hu_undulator_energy_gap_lut}
    )
