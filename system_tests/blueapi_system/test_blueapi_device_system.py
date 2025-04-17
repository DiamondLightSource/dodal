"""System test for blueapi backed device used for access control on i19.

HOWTO:
- Step 1: Start blueapi server with no stompo configuration, which mirrors
   the optics blueapi running on i19
       blueapi -c no_stomp_config.yaml serve
- Step 2: Run system tests
       tox -e system-test
"""

import pytest
from blueapi.client.client import BlueapiClient
from blueapi.config import ApplicationConfig


@pytest.fixture
def blueapi_client() -> BlueapiClient:
    return BlueapiClient.from_config(config=ApplicationConfig())
