from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from daq_config_server import ConfigClient
from daq_config_server.models.lookup_tables import GenericLookupTable
from daq_config_server.models.lookup_tables.insertion_device import (
    parse_i09_hu_undulator_energy_gap_lut,
)


@pytest.fixture
def mock_config_client(mock_config_client: ConfigClient) -> ConfigClient:
    # To Do, need a more effective way to customise this without removing other
    # behaviour like banned paths. Need to chain mock behaviour.
    # See https://github.com/DiamondLightSource/daq-config-server/issues/194
    def load_file(
        file_path: str | Path,
        desired_return_type: type[GenericLookupTable],
        reset_cached_result: bool = True,
        force_parser: Callable[[str], Any] | None = None,
    ) -> GenericLookupTable:
        with open(file_path) as f:
            contents = f.read()
        return parse_i09_hu_undulator_energy_gap_lut(contents)

    mock_config_client.get_file_contents = load_file  # type: ignore

    return mock_config_client
