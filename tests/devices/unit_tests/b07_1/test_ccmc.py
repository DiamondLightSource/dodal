import pytest
from bluesky.plan_stubs import mv
from bluesky.run_engine import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_configuration, assert_reading, assert_value

from dodal.devices.b07_1.ccmc import CCMC, CCMCPositions


@pytest.fixture
async def mock_CCMC(RE: RunEngine) -> CCMC:
    async with init_devices(mock=True):
        mock_CCMC = CCMC(prefix="", positions=CCMCPositions)
    return mock_CCMC


async def test_read_config_includes(mock_CCMC: CCMC):
    await assert_configuration(
        mock_CCMC,
        {
            f"{mock_CCMC.name}-y_rotation": {
                "value": 0.0,
            },
            f"{mock_CCMC.name}-x": {
                "value": 0.0,
            },
            f"{mock_CCMC.name}-y": {
                "value": 0.0,
            },
            f"{mock_CCMC.name}-z": {
                "value": 0.0,
            },
        },
    )


async def test_reading(mock_CCMC: CCMC):
    await assert_reading(
        mock_CCMC,
        {
            f"{mock_CCMC.name}-pos_select": {
                "value": CCMCPositions.OUT,
            },
            f"{mock_CCMC.name}-energy_in_ev": {
                "value": 0.0,
            },
        },
    )


async def test_move_crystal(
    mock_CCMC: CCMC,
    RE: RunEngine,
):
    await assert_value(mock_CCMC.pos_select, CCMCPositions.OUT.value)
    RE(mv(mock_CCMC.pos_select, CCMCPositions.XTAL_2000.value))
    await assert_value(mock_CCMC.pos_select, CCMCPositions.XTAL_2000.value)
    await assert_value(mock_CCMC.energy_in_ev, 2000.0)
