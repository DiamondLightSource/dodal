import pytest
from ophyd_async.core import DeviceCollector

from dodal.devices.i18.table import Table, TablePosition


@pytest.fixture
async def fake_table():
    async with DeviceCollector(mock=True):
        fake_thor_labs_stage = Table("", "thor_labs_stage")

    return fake_thor_labs_stage


async def test_setting_xy(fake_table: Table):
    pos = TablePosition(x=5, y=5)
    await fake_table.set(pos)


async def test_setting_xyztheta(fake_table: Table):
    pos = TablePosition(x=5, y=5, z=5, theta=5)
    await fake_table.set(pos)
