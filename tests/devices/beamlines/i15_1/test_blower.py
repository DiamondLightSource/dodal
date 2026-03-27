import pytest
from daq_config_server import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import (
    TemperatureControllerParams,
)
from ophyd_async.core import get_mock_put, init_devices, set_mock_value

from dodal.devices.beamlines.i15_1.blower import Blower
from dodal.devices.beamlines.i15_1.temperature_controller import (
    TemperatureControllerPosition,
)
from tests.test_data import TEST_XPDF_LOCAL_PARAMETERS

SAFE_POSITION = 2.0
BEAM_POSITION = 40.7


@pytest.fixture
async def blower() -> Blower:
    async with init_devices(mock=True):
        mock_blower = Blower("", ConfigClient(""), "")

    def mock_config():
        return TemperatureControllerParams(
            beam_position=BEAM_POSITION,
            safe_position=SAFE_POSITION,
            settle_time=0,
            tolerance=5.0,
            units="C",
            ramp_units="/min",
            use_calibration=True,
            use_fast_cool=None,
            calibration_file="blower_cal_10_03_2026.txt",
        )

    mock_blower.get_config = mock_config
    set_mock_value(mock_blower.motor.user_readback, 0.0)
    return mock_blower


def test_blower_gets_safe_and_beam_values_from_config(blower: Blower):
    assert blower.get_config().safe_position == SAFE_POSITION
    assert blower._safe_position == SAFE_POSITION
    assert blower.get_config().beam_position == BEAM_POSITION
    assert blower._beam_position == BEAM_POSITION


async def test_blower_moves_to_safe_value_when_set(blower: Blower):
    await blower.set(TemperatureControllerPosition.SAFE)
    get_mock_put(blower.motor.user_setpoint).assert_called_once_with(SAFE_POSITION)


async def test_blower_moves_to_beam_value_when_set(blower: Blower):
    await blower.set(TemperatureControllerPosition.BEAM)
    get_mock_put(blower.motor.user_setpoint).assert_called_once_with(BEAM_POSITION)


def test_blower_config_client_reads_config_file_successfully():
    blower = Blower("", ConfigClient(""), TEST_XPDF_LOCAL_PARAMETERS)
    assert blower.get_config() == TemperatureControllerParams(
        beam_position=44.7,
        safe_position=2.0,
        settle_time=0,
        tolerance=5.0,
        units="C",
        ramp_units="/min",
        use_calibration=True,
        use_fast_cool=None,
        calibration_file="blower_cal_10_03_2026.txt",
    )
