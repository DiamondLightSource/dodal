from unittest.mock import ANY

import numpy as np
import pytest
from bluesky.plan_stubs import abs_set
from bluesky.run_engine import RunEngine
from ophyd_async.core import StrictEnum, init_devices
from ophyd_async.testing import assert_configuration

from dodal.devices.temperture_controller import (
    Lakeshore,
)


class HEATER_SETTING(StrictEnum):
    OFF = "Off"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


@pytest.fixture
async def lakeshore():
    async with init_devices(mock=True):
        lakeshore = Lakeshore(
            prefix="007", num_readback_channel=4, heater_setting=HEATER_SETTING
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
        await lakeshore.control_channels[
            await lakeshore.control_channel.get_value()
        ].user_setpoint.get_value()
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


async def test_lakeshore_set_fail_unavailable_channel(
    lakeshore: Lakeshore, RE: RunEngine
):
    with pytest.raises(
        ValueError,
        match=f"Control channels must be between 1 and {len(lakeshore.control_channels)}.",
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
async def test_lakeshore__set_control_channel_correctly_set_up_config_and_hints(
    lakeshore: Lakeshore, RE: RunEngine, control_channel: int
):
    RE(abs_set(lakeshore.control_channel, control_channel))
    assert lakeshore.hints == {
        "fields": [
            f"lakeshore-readback-{control_channel}",
            f"lakeshore-control_channels-{control_channel}-user_setpoint",
        ],
    }
    expected_config = {
        f"lakeshore-control_channels-{control_channel}-d": {
            "value": ANY,
        },
        f"lakeshore-control_channels-{control_channel}-i": {
            "value": ANY,
        },
        f"lakeshore-control_channels-{control_channel}-p": {
            "value": ANY,
        },
        f"lakeshore-control_channels-{control_channel}-heater_output_range": {
            "value": ANY,
        },
        "lakeshore-_control_channel": {
            "value": control_channel,
        },
    }
    await assert_configuration(lakeshore, expected_config, full_match=False)
