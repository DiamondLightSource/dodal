import pytest
from ophyd_async.core import init_devices

from dodal.devices.i07.id import InsertionDevice
from dodal.devices.undulator import UndulatorOrder


@pytest.fixture
async def id() -> InsertionDevice:
    async with init_devices(mock=True):
        id = InsertionDevice(
            "ID-01",
            "ID-01",
            UndulatorOrder("harmonic"),
            "/workspaces/dodal/tests/devices/i07/IIDCalibrationTable.txt",
        )
    return id


async def test_id_gap_calculation():
    test_id = await id()
    test_id.harmonic.set(5)

    assert test_id._get_gap_to_match_energy(14) == pytest.approx(5.80, abs=0.01)
