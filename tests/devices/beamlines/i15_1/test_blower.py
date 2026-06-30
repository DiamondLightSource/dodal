import pytest
from daq_config_server import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import (
    TemperatureControllerParams,
)
from ophyd_async.core import get_mock_put, init_devices, set_mock_value

from dodal.common.enums import ValveState
from dodal.devices.beamlines.i15_1.blower import Blower
from tests.test_data import TEST_XPDF_LOCAL_PARAMETERS


@pytest.fixture
async def blower():
    async with init_devices(mock=True):
        blower = Blower("", "", "", ConfigClient(""), TEST_XPDF_LOCAL_PARAMETERS)
    return blower


def test_blower_config_client_reads_config_file_successfully(blower: Blower):
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


async def test_given_pneumatic_is_open_then_temperature_can_be_changed(blower: Blower):
    set_mock_value(blower._pneumatic, ValveState.OPEN)

    await blower.temperature.set(100)
    get_mock_put(blower._temperature_sp).assert_called_once_with(100)


async def test_given_pneumatic_is_closed_then_temperature_can_not_be_turned_on(
    blower: Blower,
):
    set_mock_value(blower._pneumatic, ValveState.CLOSED)

    with pytest.raises(ValueError):
        await blower.temperature.set(100)
    get_mock_put(blower._temperature_sp).assert_not_called()


async def test_given_pneumatic_is_closed_then_temperature_can_be_turned_off(
    blower: Blower,
):
    set_mock_value(blower._pneumatic, ValveState.CLOSED)
    set_mock_value(blower._pneumatic, ValveState.CLOSED)

    await blower.temperature.set(0)
    get_mock_put(blower._temperature_sp).assert_called_once_with(0)
