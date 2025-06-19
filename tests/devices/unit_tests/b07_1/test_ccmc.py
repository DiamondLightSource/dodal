from unittest.mock import ANY

import pytest
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, assert_value, set_mock_value

from dodal.devices.b07_1.ccmc import Ccmc, CcmcPositions


@pytest.fixture
async def mock_ccmc(RE: RunEngine) -> Ccmc:
    async with init_devices(mock=True):
        ccmc = Ccmc(prefix="CCM-01")
    return ccmc


@pytest.mark.parametrize(
    "key",
    [
        "pos_select",
        "x",
        "y",
        "z",
        "y_rotation",
    ],
)
async def test_describe_includes(
    mock_ccmc: Ccmc,
    key: str,
):
    description = await mock_ccmc.describe()
    reading = await mock_ccmc.read()

    assert f"{mock_ccmc.name}-{key}" in description
    assert f"{mock_ccmc.name}-{key}" in reading


async def test_reading(mock_ccmc: Ccmc):
    await assert_reading(
        mock_ccmc,
        {
            f"{mock_ccmc.name}-pos_select": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": CcmcPositions.OUT.value,
            },
            f"{mock_ccmc.name}-x": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            f"{mock_ccmc.name}-y": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            f"{mock_ccmc.name}-y_rotation": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
            f"{mock_ccmc.name}-z": {
                "alarm_severity": 0,
                "timestamp": ANY,
                "value": 0.0,
            },
        },
    )


async def test_move_crystal(mock_ccmc: Ccmc):
    await assert_value(mock_ccmc.pos_select, CcmcPositions.OUT.value)
    set_mock_value(mock_ccmc.pos_select, CcmcPositions.XTAL_2000.value)
    await assert_value(mock_ccmc.pos_select, CcmcPositions.XTAL_2000.value)
