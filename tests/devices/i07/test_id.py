import pytest
from ophyd_async.core import init_devices

from dodal.devices.i07.id import InsertionDevice
from dodal.devices.undulator import UndulatorOrder
from tests.devices.i07 import TEST_LOOKUP_TABLE_PATH


@pytest.fixture
async def id() -> InsertionDevice:
    async with init_devices(mock=True):
        id = InsertionDevice(
            "ID-01",
            "ID-01",
            UndulatorOrder("harmonic"),
            TEST_LOOKUP_TABLE_PATH,
        )
    return id


@pytest.mark.parametrize(
    "energy_kev, gap",
    [(14, 5.81), (15, 6.25)],
)
async def test_id_gap_calculation(energy_kev: float, gap: float, id: InsertionDevice):
    id.harmonic.set(5)
    interpolated_gap: float = await id._get_gap_to_match_energy(energy_kev)
    assert interpolated_gap == pytest.approx(gap, abs=0.01)
