"""System test for blueapi backed device used for access control on i19.

HOWTO:
- Step 1: Start blueapi server with no stompo configuration, which mirrors
   the optics blueapi running on i19
       blueapi -c no_stomp_config.yaml serve
- Step 2: Run system tests
       tox -e system-test
"""

import time

import pytest
from blueapi.client.client import BlueapiClient
from blueapi.config import ApplicationConfig

from .example_devices_and_plans import AccessControlledOpticsMotors


@pytest.fixture(scope="module", autouse=True)
def wait_for_server():
    client = BlueapiClient.from_config(config=ApplicationConfig())

    for _ in range(20):
        try:
            client.get_environment()
            return
        except ConnectionError:
            ...
        time.sleep(0.5)
    raise TimeoutError("No connection to blueapi server")


@pytest.fixture
def blueapi_client() -> BlueapiClient:
    return BlueapiClient.from_config(config=ApplicationConfig())


@pytest.fixture
async def motors_with_blueapi() -> AccessControlledOpticsMotors:
    ac_motors = AccessControlledOpticsMotors(name="motors_with_blueapi")
    await ac_motors.connect()
    return ac_motors
