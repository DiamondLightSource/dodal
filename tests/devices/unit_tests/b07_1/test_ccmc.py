import re

import pytest
from bluesky import FailedStatus
from bluesky.plan_stubs import mv
from bluesky.run_engine import RunEngine
from ophyd_async.core import StrictEnum, init_devices
from ophyd_async.testing import (
    assert_configuration,
    assert_reading,
    assert_value,
    partial_reading,
)

from dodal.devices.b07_1.ccmc import (
    ChannelCutMonochromator,
    ChannelCutMonochromatorPositions,
)


class WrongEnum(StrictEnum):
    POS_100 = "100.0"


@pytest.fixture
async def mock_ccmc() -> ChannelCutMonochromator:
    async with init_devices(mock=True):
        mock_ccmc = ChannelCutMonochromator(prefix="")
    return mock_ccmc


async def test_read_config_includes(mock_ccmc: ChannelCutMonochromator):
    await assert_configuration(
        mock_ccmc,
        {
            f"{mock_ccmc.name}-_xyz-x-motor_egu": partial_reading(""),
            f"{mock_ccmc.name}-_xyz-x-offset": partial_reading(0.0),
            f"{mock_ccmc.name}-_xyz-x-velocity": partial_reading(0.0),
            f"{mock_ccmc.name}-_xyz-y-motor_egu": partial_reading(""),
            f"{mock_ccmc.name}-_xyz-y-offset": partial_reading(0.0),
            f"{mock_ccmc.name}-_xyz-y-velocity": partial_reading(0.0),
            f"{mock_ccmc.name}-_xyz-z-motor_egu": partial_reading(""),
            f"{mock_ccmc.name}-_xyz-z-offset": partial_reading(0.0),
            f"{mock_ccmc.name}-_xyz-z-velocity": partial_reading(0.0),
        },
    )


async def test_reading(mock_ccmc: ChannelCutMonochromator):
    await assert_reading(
        mock_ccmc,
        {
            f"{mock_ccmc.name}-crystal": partial_reading(
                ChannelCutMonochromatorPositions.OUT
            ),
            f"{mock_ccmc.name}-_xyz-x": partial_reading(0.0),
            f"{mock_ccmc.name}-_xyz-y": partial_reading(0.0),
            f"{mock_ccmc.name}-_xyz-z": partial_reading(0.0),
            f"{mock_ccmc.name}-_y_rotation": partial_reading(0.0),
        },
    )


async def test_move_crystal(
    mock_ccmc: ChannelCutMonochromator,
    RE: RunEngine,
):
    await assert_value(mock_ccmc.crystal, ChannelCutMonochromatorPositions.OUT)
    RE(mv(mock_ccmc, ChannelCutMonochromatorPositions.XTAL_2000))
    await assert_value(mock_ccmc.crystal, ChannelCutMonochromatorPositions.XTAL_2000)


@pytest.mark.parametrize(
    "position",
    list(ChannelCutMonochromatorPositions),
    ids=[c.name for c in ChannelCutMonochromatorPositions],
)
async def test_get_energy_in_ev(
    position: ChannelCutMonochromatorPositions,
    mock_ccmc: ChannelCutMonochromator,
):
    if position == ChannelCutMonochromatorPositions.OUT:
        await mock_ccmc.set(position)
        with pytest.raises(ValueError):
            await mock_ccmc.energy_in_ev.get_value()
    else:
        await mock_ccmc.set(position)
        await assert_value(
            mock_ccmc.energy_in_ev, float(str(position.value).split("Xtal_")[1])
        )


async def test_move_crystal_wrong_position_ignored(mock_ccmc: ChannelCutMonochromator):
    await assert_value(mock_ccmc.crystal, ChannelCutMonochromatorPositions.OUT)
    with pytest.raises(ValueError):
        await mock_ccmc.set(WrongEnum.POS_100)  # type: ignore
    await assert_value(mock_ccmc.crystal, ChannelCutMonochromatorPositions.OUT)


async def test_move_crystal_wrong_position_re_error(
    mock_ccmc: ChannelCutMonochromator,
    RE: RunEngine,
):
    await assert_value(mock_ccmc.crystal, ChannelCutMonochromatorPositions.OUT)
    with pytest.raises(
        FailedStatus,
        match=re.escape("is not a valid ChannelCutMonochromatorPositions"),
    ):
        RE(mv(mock_ccmc, WrongEnum.POS_100))
