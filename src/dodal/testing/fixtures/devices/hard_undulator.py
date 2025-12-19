from unittest.mock import MagicMock

import pytest
from daq_config_server.client import ConfigServer

from dodal.devices.i09_1_shared import get_convert_lut

lut = {
    "column_names": [
        "order",
        "ring_energy_gev",
        "magnetic_field_t",
        "energy_min_eV",
        "energy_max_eV",
        "gap_min_mm",
        "gap_max_mm",
        "gap_offset_mm",
    ],
    "rows": [
        [1, 3.00089, 0.98928, 2.12, 3.05, 14.265, 23.72, 0.0],
        [2, 3.04129, 1.02504, 2.5, 2.8, 5.05165, 8.88007, 0.0],
        [3, 3.05798, 1.03065, 2.4, 4.3, 5.2, 8.99036, 0.0],
        [4, 3.03635, 1.02332, 3.2, 5.7, 5.26183, 8.9964, 0.0],
        [5, 3.06334, 1.03294, 4.0, 7.2, 5.22735, 9.02065, 0.0],
        [6, 3.04963, 1.02913, 4.7, 8.6, 5.13939, 9.02527, 0.0],
        [7, 3.06515, 1.03339, 5.5, 10.1, 5.12684, 9.02602, 0.0],
        [8, 3.05775, 1.03223, 6.3, 11.5, 5.16289, 9.02873, 0.0],
        [9, 3.06829, 1.03468, 7.1, 13.0, 5.16357, 9.03049, 0.0],
        [10, 3.06164, 1.03328, 7.9, 14.4, 5.17205, 9.02845, 0.0],
        [11, 3.07056, 1.03557, 8.6, 15.9, 5.1135, 9.0475, 0.0],
        [12, 3.06627, 1.03482, 9.4, 17.3, 5.12051, 9.02826, 0.0],
        [13, 3.07176, 1.03623, 10.2, 18.3, 5.13027, 8.8494, 0.0],
        [14, 3.06964, 1.03587, 11.0, 18.3, 5.13985, 8.30146, 0.0],
        [15, 3.06515, 1.03391, 11.8, 18.3, 5.14643, 7.8238, 0.0],
    ],
}


@pytest.fixture
def mock_config_client() -> ConfigServer:
    mock_config_client = ConfigServer()
    mock_config_client.get_file_contents = MagicMock(spec=["get_file_contents"])

    def my_side_effect(file_path, reset_cached_result) -> dict:
        assert reset_cached_result is True
        return lut

    mock_config_client.get_file_contents.side_effect = my_side_effect
    return mock_config_client


@pytest.fixture
def lut_dictionary(
    mock_config_client: ConfigServer,
) -> dict:
    return get_convert_lut(mock_config_client, "")
