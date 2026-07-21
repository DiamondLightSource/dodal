from typing import TypeVar

import pytest
from daq_config_server.client import ConfigClient
from daq_config_server.models import ConfigModel

T = TypeVar("T", str, dict, ConfigModel)


TModel = TypeVar("TModel", bound=ConfigModel)


@pytest.fixture
def path_to_mock_data() -> dict:
    return {}


@pytest.fixture
def mock_config_client(path_to_mock_data) -> ConfigClient:
    config_client = ConfigClient()
    config_client.configure_mock(path_to_mock_data)
    return config_client
