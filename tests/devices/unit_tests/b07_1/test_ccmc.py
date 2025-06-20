from unittest.mock import ANY

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, assert_value, set_mock_value

from dodal.devices.b07_1.ccmc import CCMC, CCMCPositions


@pytest.fixture
async def mock_CCMC(RE: RunEngine) -> CCMC:
    async with init_devices(mock=True):
        mock_CCMC = CCMC(prefix="CCM-01")
    return mock_CCMC


async def test_describe_includes(
    mock_CCMC: CCMC,
):
    description = await mock_CCMC.describe()
    reading = await mock_CCMC.read()

    expected_keys: list[str] = [
        "pos_select",
        "x",
        "y",
        "z",
        "y_rotation",
    ]

    for key in expected_keys:
        assert f"{mock_CCMC.name}-{key}" in reading
        assert f"{mock_CCMC.name}-{key}" in description


async def test_reading(mock_CCMC: CCMC):
    await assert_reading(
        mock_CCMC,
        {
            f"{mock_CCMC.name}-pos_select": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": CCMCPositions.OUT.value,
            },
            f"{mock_CCMC.name}-x": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            f"{mock_CCMC.name}-y": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            f"{mock_CCMC.name}-y_rotation": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            f"{mock_CCMC.name}-z": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
        },
    )


async def test_move_crystal(mock_CCMC: CCMC):
    await assert_value(mock_CCMC.pos_select, CCMCPositions.OUT.value)
    set_mock_value(mock_CCMC.pos_select, CCMCPositions.XTAL_2000.value)
    await assert_value(mock_CCMC.pos_select, CCMCPositions.XTAL_2000.value)
