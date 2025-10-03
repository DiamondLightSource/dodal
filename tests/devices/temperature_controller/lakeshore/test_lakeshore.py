from collections import defaultdict
from typing import Any
from unittest.mock import ANY

import numpy as np
import pytest
from bluesky.plan_stubs import abs_set
from bluesky.plans import count
from bluesky.run_engine import RunEngine
from ophyd_async.core import StrictEnum, init_devices
from ophyd_async.testing import assert_configuration, assert_reading

from dodal.devices.temperture_controller import (
    Lakeshore,
)


class HeaterSettings(StrictEnum):
    OFF = "Off"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


@pytest.fixture
async def lakeshore() -> Lakeshore:
    async with init_devices(mock=True):
        lakeshore = Lakeshore(
            prefix="007", num_readback_channel=4, heater_setting=HeaterSettings
        )
    return lakeshore


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
async def test_lakeshore_set_fail_outside_limit(
    lakeshore: Lakeshore, RE: RunEngine, temperature: float
):
    low = await lakeshore.temperature_low_limit.get_value()
    high = await lakeshore.temperature_high_limit.get_value()
    with pytest.raises(
        ValueError,
        match=f"{lakeshore.name} requested temperature {temperature} is outside limits: {low}, {high}",
    ):
        await lakeshore.set(temperature)


async def test_lakeshore_set_fail_unavailable_channel(
    lakeshore: Lakeshore, RE: RunEngine
):
    with pytest.raises(
        ValueError,
        match=f"Control channel must be between 1 and {len(lakeshore.control_channels)}.",
    ):
        await lakeshore._set_control_channel(0)


@pytest.mark.parametrize(
    "control_channel",
    [1, 2, 3, 4],
)
async def test_lakeshore_set_control_channel_correctly_set_up_config(
    lakeshore: Lakeshore,
    RE: RunEngine,
    control_channel: int,
):
    RE(abs_set(lakeshore.control_channel, control_channel, wait=True))

    config = ["user_setpoint", "p", "i", "d", "heater_output_range"]
    expected_config: dict[str, dict[str, Any]] = {
        f"lakeshore-control_channels-{control_channel}-{pv}": {"value": ANY}
        for pv in config
    }
    expected_config["lakeshore-_control_channel"] = {
        "value": control_channel,
    }
    await assert_configuration(lakeshore, expected_config, full_match=False)


async def test_lakeshore_read(
    lakeshore: Lakeshore,
):
    expected_reading = {}

    for control_channel in range(1, 5):
        expected_reading[
            f"lakeshore-control_channels-{control_channel}-user_setpoint"
        ] = {"value": ANY}

        expected_reading[f"lakeshore-readback-{control_channel}"] = {
            "value": ANY,
        }
    await assert_reading(lakeshore, expected_reading, full_match=False)


async def test_lakeshore_hints_with_count(lakeshore: Lakeshore, RE: RunEngine):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(count([lakeshore]), capture_emitted)
    for i in range(1, 5):
        assert (
            docs["descriptor"][0]["hints"]["lakeshore"]["fields"][i - 1]
            == f"lakeshore-readback-{i}"
        )
