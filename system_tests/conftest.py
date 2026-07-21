import pytest
from daq_config_server.client import ConfigClient

# Add run_engine to be used in system tests
pytest_plugins = ["dodal.testing.fixtures.run_engine"]


@pytest.fixture
def mock_config_client() -> ConfigClient:
    config_client = ConfigClient()
    config_client.configure_mock()
    return config_client
