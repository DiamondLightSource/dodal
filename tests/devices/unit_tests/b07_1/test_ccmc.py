import re

import pytest
from bluesky.plan_stubs import mv
from bluesky.run_engine import RunEngine
from ophyd_async.core import StrictEnum, init_devices
from ophyd_async.testing import assert_configuration, assert_reading, assert_value

from dodal.devices.b07_1.ccmc import CCMC, CCMCPositions


class WrongEnum(StrictEnum):
    POS_100 = 100.0


@pytest.fixture
async def mock_ccmc(RE: RunEngine) -> CCMC:
    async with init_devices(mock=True):
        mock_ccmc = CCMC(prefix="", positions=CCMCPositions)
    return mock_ccmc


async def test_read_config_includes(mock_ccmc: CCMC):
    await assert_configuration(
        mock_ccmc,
        {
            f"{mock_ccmc.name}-y_rotation": {"value": 0.0},
            f"{mock_ccmc.name}-x-motor_egu": {"value": ""},
            f"{mock_ccmc.name}-x-offset": {"value": 0.0},
            f"{mock_ccmc.name}-x-velocity": {"value": 0.0},
            f"{mock_ccmc.name}-y-motor_egu": {"value": ""},
            f"{mock_ccmc.name}-y-offset": {"value": 0.0},
            f"{mock_ccmc.name}-y-velocity": {"value": 0.0},
            f"{mock_ccmc.name}-z-motor_egu": {"value": ""},
            f"{mock_ccmc.name}-z-offset": {"value": 0.0},
            f"{mock_ccmc.name}-z-velocity": {"value": 0.0},
        },
    )


async def test_reading(mock_ccmc: CCMC):
    await assert_reading(
        mock_ccmc,
        {
            f"{mock_ccmc.name}-crystal": {"value": CCMCPositions.OUT},
            f"{mock_ccmc.name}-x": {"value": 0.0},
            f"{mock_ccmc.name}-y": {"value": 0.0},
            f"{mock_ccmc.name}-z": {"value": 0.0},
        },
    )


async def test_move_crystal(
    mock_ccmc: CCMC,
    RE: RunEngine,
):
    await assert_value(mock_ccmc.crystal, CCMCPositions.OUT)
    RE(mv(mock_ccmc.crystal, CCMCPositions.XTAL_2000))
    await assert_value(mock_ccmc.crystal, CCMCPositions.XTAL_2000)
    with pytest.raises(
        ValueError,
        match=re.escape("is not a valid CCMCPositions"),
    ):
        await mock_ccmc.crystal.set(WrongEnum.POS_100)


@pytest.mark.parametrize(
    "position", list(CCMCPositions), ids=[c.name for c in CCMCPositions]
)
async def test_get_energy_in_ev(
    position: CCMCPositions,
    mock_ccmc: CCMC,
):
    if position == CCMCPositions.OUT:
        await mock_ccmc.crystal.set(position)
        with pytest.raises(ValueError):
            await mock_ccmc.energy_in_ev.get_value()
    else:
        await mock_ccmc.crystal.set(position)
        await assert_value(
            mock_ccmc.energy_in_ev, float(str(position.value).split("Xtal_")[1])
        )
