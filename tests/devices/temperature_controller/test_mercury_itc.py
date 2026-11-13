import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_configuration, assert_reading, partial_reading

from dodal.devices.temperature_controller.mercury_itc import MercuryITC


@pytest.fixture
async def mock_mercury():
    with init_devices(mock=True):
        fake_aperture = MercuryITC("test_prefix", "mock_mercury")
    return fake_aperture


async def test_mercury_can_be_read(mock_mercury: MercuryITC):
    set_mock_value(mock_mercury.user_setpoint, 75)
    set_mock_value(mock_mercury.heater_output, 50)
    set_mock_value(mock_mercury.readback, 75.6)

    await assert_reading(
        mock_mercury,
        {"mock_mercury-readback": partial_reading(75.6)},
    )

    await assert_configuration(
        mock_mercury,
        {
            "mock_mercury-user_setpoint": partial_reading(75),
            "mock_mercury-heater_output": partial_reading(50),
        },
    )
