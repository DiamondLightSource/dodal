import pytest
from daq_config_server import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import (
    TemperatureControllerParams,
)
from ophyd_async.core import get_mock_put, init_devices, set_mock_value

from dodal.devices.beamlines.i15_1.cobra import Cobra
from dodal.devices.beamlines.i15_1.temperature_controller import (
    TemperatureControllerPosition,
)


@pytest.fixture
async def cobra() -> Cobra:
    async with init_devices(mock=True):
        mock_cobra = Cobra("", ConfigClient(""), "")

    def mock_config():
        return TemperatureControllerParams(
            beam_position=400.5,
            safe_position=5.0,
            settle_time=600,
            tolerance=5.0,
            units="K",
            ramp_units="/h",
            use_calibration=True,
            use_fast_cool=True,
            calibration_file="cobra_calibration_2025-09-11.txt",
        )

    mock_cobra.get_config = mock_config
    set_mock_value(mock_cobra.motor.user_readback, 0.0)
    return mock_cobra


def test_cobra_gets_safe_value_from_config(cobra: Cobra):
    expected_safe_position = 5.0
    assert cobra.get_config().safe_position == expected_safe_position
    assert cobra._safe_position == expected_safe_position


async def test_cobra_moves_to_safe_value_when_set(cobra: Cobra):
    await cobra.set(TemperatureControllerPosition.SAFE)
    get_mock_put(cobra.motor.user_setpoint).assert_called_once_with(5.0)


async def test_cobra_moves_to_beam_value_when_set(cobra: Cobra):
    await cobra.set(TemperatureControllerPosition.BEAM)
    get_mock_put(cobra.motor.user_setpoint).assert_called_once_with(400.5)
