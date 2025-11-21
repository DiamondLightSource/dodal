import json
from pathlib import Path

import pytest
from daq_config_server.client import ConfigServer

from dodal.devices.util.lookup_tables_apple2 import (
    EnergyMotorLookup,
    LookupTable,
    LookupTableConfig,
    convert_csv_to_lookup,
)
from tests.devices.i21.test_data import (
    EXPECTED_ID_ENERGY_2_GAP_CALIBRATIONS_JSON,
    ID_ENERGY_2_GAP_CALIBRATIONS_CSV,
)


@pytest.fixture
def mock_i21_energy_motor_lookup(
    mock_config_client: ConfigServer,
) -> EnergyMotorLookup:
    return EnergyMotorLookup(
        config_client=mock_config_client,
        lut_config=LookupTableConfig(grading="Grating"),
        gap_path=Path(ID_ENERGY_2_GAP_CALIBRATIONS_CSV),
    )


def test_21_energy_motor_lookup_convert_csv_to_lookup_success(
    mock_i21_energy_motor_lookup: EnergyMotorLookup,
):
    file = mock_i21_energy_motor_lookup.config_client.get_file_contents(
        file_path=ID_ENERGY_2_GAP_CALIBRATIONS_CSV, reset_cached_result=True
    )
    data = convert_csv_to_lookup(
        file_contents=file,
        lut_config=LookupTableConfig(grading="Grating"),
        skip_line_start_with="#",
    )

    with open(EXPECTED_ID_ENERGY_2_GAP_CALIBRATIONS_JSON, "rb") as f:
        loaded_dict = LookupTable(json.load(f))
    assert data == loaded_dict
