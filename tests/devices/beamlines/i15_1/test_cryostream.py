import pytest
from daq_config_server import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import (
    TemperatureControllerParams,
)
from ophyd_async.core import get_mock_put, init_devices, set_mock_value

from dodal.devices.beamlines.i15_1.cryostream import Cryostream
from dodal.devices.beamlines.i15_1.temperature_controller import (
    TemperatureControllerPosition,
)


@pytest.fixture
async def cryostream() -> Cryostream:
    async with init_devices(mock=True):
        mock_cryostream = Cryostream("", ConfigClient(""), "")

    def mock_config():
        return TemperatureControllerParams(
            beam_position=450.9,
            safe_position=0.0,
            settle_time=600,
            tolerance=0.5,
            units="K",
            ramp_units="/h",
            use_calibration=True,
            use_fast_cool=None,
            calibration_file="cryostream_cal_2025-01-23.txt",
        )

    mock_cryostream.get_config = mock_config
    set_mock_value(mock_cryostream.motor.user_readback, 0.0)
    return mock_cryostream


def test_cryostream_gets_safe_value_from_config(cryostream: Cryostream):
    expected_safe_position = 0.0
    assert cryostream.get_config().safe_position == expected_safe_position
    assert cryostream._safe_position == expected_safe_position


async def test_cryostream_moves_to_safe_value_when_set(cryostream: Cryostream):
    await cryostream.set(TemperatureControllerPosition.SAFE)
    get_mock_put(cryostream.motor.user_setpoint).assert_called_once_with(0.0)


async def test_cryostream_moves_to_beam_value_when_set(cryostream: Cryostream):
    await cryostream.set(TemperatureControllerPosition.BEAM)
    get_mock_put(cryostream.motor.user_setpoint).assert_called_once_with(450.9)
