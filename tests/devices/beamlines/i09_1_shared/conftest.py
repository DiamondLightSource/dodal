import pytest
from daq_config_server.models.lookup_tables.insertion_device import (
    parse_i09_hu_undulator_energy_gap_lut,
)

from tests.devices.beamlines.i09_1_shared.test_data import TEST_HARD_UNDULATOR_LUT


@pytest.fixture
def path_to_mock_data() -> dict:
    with open(TEST_HARD_UNDULATOR_LUT) as f:
        contents = f.read()
    return {TEST_HARD_UNDULATOR_LUT: parse_i09_hu_undulator_energy_gap_lut(contents)}
