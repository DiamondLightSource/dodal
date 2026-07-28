import pytest
from daq_config_server.client import ConfigClient
from daq_config_server.testing import MockServerResponse

# Add run_engine to be used in system tests
pytest_plugins = ["dodal.testing.fixtures.run_engine"]


@pytest.fixture
def mock_config_client() -> ConfigClient:
    return ConfigClient(server_response=MockServerResponse())
