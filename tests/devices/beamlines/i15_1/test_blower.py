from unittest.mock import AsyncMock, patch

import pytest
from daq_config_server.client import ConfigClient
from daq_config_server.models.i15_1.xpdf_parameters import (
    TemperatureControllerParams,
)
from ophyd_async.core import (
    callback_on_mock_put,
    get_mock_put,
    init_devices,
    set_mock_value,
)
from ophyd_async.testing import assert_reading, partial_reading

from dodal.common.enums import ValveState
from dodal.devices.beamlines.i15_1.blower import Blower, CalibratedBlower
from tests.test_data import (
    TEST_I15_1_TEMPERATURE_CALIBRATION,
    TEST_XPDF_LOCAL_PARAMETERS,
)


@pytest.fixture
async def blower(mock_config_client: ConfigClient):
    async with init_devices(mock=True):
        blower = Blower("", "", "", mock_config_client, TEST_XPDF_LOCAL_PARAMETERS)
    set_mock_value(blower.settle_time_s, 0)
    return blower


@pytest.fixture
async def calibrated_blower(mock_config_client: ConfigClient):
    async with init_devices(mock=True):
        blower = CalibratedBlower(
            "",
            "",
            "",
            mock_config_client,
            TEST_XPDF_LOCAL_PARAMETERS,
            TEST_I15_1_TEMPERATURE_CALIBRATION,
        )
    set_mock_value(blower.settle_time_s, 0)
    set_mock_value(blower.raw_temperature._pneumatic, ValveState.OPEN)
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
    set_mock_value(blower.raw_temperature._pneumatic, ValveState.OPEN)

    await blower.temperature.set(100)
    get_mock_put(blower.raw_temperature._temperature_sp).assert_called_once_with(100)


async def test_given_pneumatic_is_closed_then_temperature_can_not_be_turned_on(
    blower: Blower,
):
    set_mock_value(blower.raw_temperature._pneumatic, ValveState.CLOSED)

    with pytest.raises(ValueError):
        await blower.temperature.set(100)
    get_mock_put(blower.raw_temperature._temperature_sp).assert_not_called()


async def test_given_pneumatic_is_closed_then_temperature_can_be_turned_off(
    blower: Blower,
):
    set_mock_value(blower.raw_temperature._pneumatic, ValveState.CLOSED)

    await blower.temperature.set(0)
    get_mock_put(blower.raw_temperature._temperature_sp).assert_called_once_with(0)


async def test_when_temperature_is_read_then_read_underlying_pv(
    blower: Blower,
):
    set_mock_value(blower.raw_temperature._temperature_rbv, 100)

    await assert_reading(
        blower.temperature,
        {
            "blower-temperature": partial_reading(100),
        },
    )


async def test_settle_time_is_awaited_after_temperature_change(blower: Blower):
    set_mock_value(blower.raw_temperature._pneumatic, ValveState.OPEN)
    set_mock_value(blower.settle_time_s, 1.5)

    with patch(
        "dodal.devices.beamlines.i15_1.blower.asyncio.sleep",
        new_callable=AsyncMock,
    ) as mock_sleep:
        await blower.temperature.set(100)

    assert await blower.raw_temperature._temperature_rbv.get_value() == 100

    mock_sleep.assert_any_call(1.5)


async def test_settle_time_is_not_awaited_when_turning_off(
    blower: Blower,
):
    set_mock_value(blower.settle_time_s, 1.5)

    with patch(
        "dodal.devices.beamlines.i15_1.blower.asyncio.sleep",
        new_callable=AsyncMock,
    ) as mock_sleep:
        await blower.temperature.set(0)

    # Sleep still has a single call from the callback mocking
    mock_sleep.assert_called_once_with(0)


async def test_stop_sets_temperature_to_zero(blower: Blower):
    await blower.raw_temperature.movable_logic.stop()
    get_mock_put(blower.raw_temperature._temperature_sp).assert_called_once_with(0)


async def test_temperature_times_out_if_readback_does_not_change(blower: Blower):
    set_mock_value(blower.raw_temperature._pneumatic, ValveState.OPEN)

    def null_callback(*_, **__):
        return None

    callback_on_mock_put(blower.raw_temperature._temperature_sp, null_callback)

    with patch(
        "dodal.devices.beamlines.i15_1.blower.TemperatureMoveLogic.TIMEOUT",
        new=0.01,
    ):
        with pytest.raises(TimeoutError):
            await blower.temperature.set(100)


async def test_calibrated_blower_sets_raw_temperature_based_on_calibration(
    calibrated_blower: CalibratedBlower,
):
    await calibrated_blower.temperature.set(500)
    get_mock_put(
        calibrated_blower.raw_temperature._temperature_sp
    ).assert_called_once_with(759.721816599402)


async def test_calibrated_blower_returns_calibrated_temperature_based_on_raw(
    calibrated_blower: CalibratedBlower,
):
    await calibrated_blower.raw_temperature.set(759.721816599402)
    assert await calibrated_blower.temperature.get_value() == pytest.approx(500)
