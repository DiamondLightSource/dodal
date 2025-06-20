from collections.abc import Mapping
from typing import Any
from unittest.mock import ANY

import pytest
from ophyd_async.core import StandardReadable, init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.base_table import PitchedBaseTable


@pytest.fixture
async def pitched_base_table() -> PitchedBaseTable:
    async with init_devices(mock=True):
        pitched_base_table = PitchedBaseTable("DEMO-STABL-01:")

    return pitched_base_table


async def test_reading_basetable_reads_pos_and_pitch(
    pitched_base_table: PitchedBaseTable,
):
    set_mock_value(pitched_base_table.x.user_readback, 10.0)
    set_mock_value(pitched_base_table.y.user_readback, 20.0)
    set_mock_value(pitched_base_table.pitch.user_readback, 0.5)

    await assert_reading(
        pitched_base_table,
        {
            "basetable-x": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            "slits-y": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 20.0,
            },
            "slits-pitch": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.5,
            },
        },
    )


async def assert_reading(
    device: StandardReadable,
    expected_reading: Mapping[str, Any],
) -> None:
    reading = await device.read()

    assert reading == expected_reading
