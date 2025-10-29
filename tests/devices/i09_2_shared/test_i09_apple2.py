import pickle
from unittest import mock
from unittest.mock import MagicMock

import pytest
from daq_config_server.client import ConfigServer

from dodal.devices.i09_2_shared.i09_apple2 import J09EnergyMotorLookup
from dodal.devices.util.lookup_tables_apple2 import convert_csv_to_lookup
from tests.devices.i09_2_shared.test_data import (
    LOOKUP_TABLE_PATH,
    TEST_EXPECTED_ENERGY_MOTOR_LOOKUP,
    TEST_EXPECTED_UNDULATOR_LUT,
    TEST_SOFT_UNDULATOR_LUT,
)


@pytest.fixture
def mock_config_client() -> ConfigServer:
    mock.patch("dodal.devices.i09_shared.i09_apple2.ConfigServer")
    mock_config_client = ConfigServer()

    mock_config_client.get_file_contents = MagicMock(spec=["get_file_contents"])

    def my_side_effect(file_path, reset_cached_result) -> str:
        assert reset_cached_result is True
        with open(file_path) as f:
            return f.read()

    mock_config_client.get_file_contents.side_effect = my_side_effect
    return mock_config_client


@pytest.fixture
def mock_j09_energy_motor_lookup(mock_config_client) -> J09EnergyMotorLookup:
    return J09EnergyMotorLookup(
        lookuptable_dir=LOOKUP_TABLE_PATH,
        gap_file_name="JIDEnergy2GapCalibrations.csv",
        config_client=mock_config_client,
        poly_deg=[
            "9th-order",
            "8th-order",
            "7th-order",
            "6th-order",
            "5th-order",
            "4th-order",
            "3rd-order",
            "2nd-order",
            "1st-order",
            "0th-order",
        ],
    )


def test_j09_energy_motor_lookup_convert_csv_to_lookup_success(
    mock_j09_energy_motor_lookup: J09EnergyMotorLookup,
):
    file = mock_j09_energy_motor_lookup.config_client.get_file_contents(
        file_path=TEST_SOFT_UNDULATOR_LUT, reset_cached_result=True
    )
    data = convert_csv_to_lookup(
        file=file,
        source=None,
        poly_deg=[
            "9th-order",
            "8th-order",
            "7th-order",
            "6th-order",
            "5th-order",
            "4th-order",
            "3rd-order",
            "2nd-order",
            "1st-order",
            "0th-order",
        ],
        skip_line_start_with="#",
    )
    with open(TEST_EXPECTED_UNDULATOR_LUT, "rb") as f:
        loaded_dict = pickle.load(f)
    assert data == loaded_dict


def test_j09_energy_motor_lookup_update_lookuptable(
    mock_j09_energy_motor_lookup: J09EnergyMotorLookup,
):
    mock_j09_energy_motor_lookup.update_lookuptable()

    with open(TEST_EXPECTED_ENERGY_MOTOR_LOOKUP, "rb") as f:
        map_dict = pickle.load(f)

    assert mock_j09_energy_motor_lookup.lookup_tables == map_dict
