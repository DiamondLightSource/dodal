from unittest.mock import ANY

import numpy as np
import pytest
from bluesky.plan_stubs import abs_set
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_configuration

from dodal.devices.temperture_controller import (
    LAKESHORE336_HEATER_SETTING,
    Lakeshore,
)


@pytest.fixture
async def lakeshore():
    async with init_devices(mock=True):
        lakeshore = Lakeshore(
            prefix="007", no_channels=4, heater_setting=LAKESHORE336_HEATER_SETTING
        )

    yield lakeshore


@pytest.mark.parametrize(
    "control_channel",
    [
        1,
        2,
        3,
        4,
    ],
)
async def test_lakeshore_set_success(
    lakeshore: Lakeshore, RE: RunEngine, control_channel: int
):
    RE(abs_set(lakeshore.control_channel, control_channel, wait=True))
    temperature = np.random.uniform(10, 400)
    RE(abs_set(lakeshore, temperature, wait=True))

    assert (
        await lakeshore.temperature.user_setpoint[
            await lakeshore.control_channel.get_value()
        ].get_value()
        == temperature
    )


@pytest.mark.parametrize(
    "temperature",
    [
        -2,
        500,
    ],
)
async def test_lakeshore_set_success_fail_outside_limit(
    lakeshore: Lakeshore, RE: RunEngine, temperature: float
):
    with pytest.raises(
        ValueError, match="Requested temperature must be withing 400.0 and 0.0"
    ):
        await lakeshore.set(temperature)


async def test_lakeshore_set_success_fail_unavailable_channel(
    lakeshore: Lakeshore, RE: RunEngine
):
    with pytest.raises(
        ValueError,
        match=f"Control channels must be between 1 and {len(lakeshore.PID.p)}.",
    ):
        await lakeshore._set_control_channel(0)


@pytest.mark.parametrize(
    "control_channel",
    [
        1,
        2,
        3,
        4,
    ],
)
async def test_lakeshore__set_control_channel_correctly_set_up_readableFormat(
    lakeshore: Lakeshore, RE: RunEngine, control_channel: int
):
    RE(abs_set(lakeshore.control_channel, control_channel, wait=True))
    assert lakeshore.hints == {
        "fields": [
            f"lakeshore-temperature-user_readback-{control_channel}",
            f"lakeshore-temperature-user_setpoint-{control_channel}",
        ],
    }
    expected_config = {
        f"lakeshore-PID-d-{control_channel}": {
            "value": ANY,
        },
        f"lakeshore-PID-i-{control_channel}": {
            "value": ANY,
        },
        f"lakeshore-PID-p-{control_channel}": {
            "value": ANY,
        },
        "lakeshore-_control_channel": {
            "value": control_channel,
        },
    }
    await assert_configuration(lakeshore, expected_config, full_match=False)
