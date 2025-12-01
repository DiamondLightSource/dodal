import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_value

from dodal.devices.common_dcm import (
    DoubleCrystalMonochromatorBase,
    PitchAndRollCrystal,
    RollCrystal,
    StationaryCrystal,
)


def test_make_crystals():
    dcm = DoubleCrystalMonochromatorBase("prefix:", RollCrystal, RollCrystal)
    assert dcm.xtal_1.roll_in_mrad.user_setpoint.source == "ca://prefix:XTAL1:ROLL.VAL"
    dcm = DoubleCrystalMonochromatorBase("prefix:", RollCrystal, StationaryCrystal)
    assert dcm.xtal_1.roll_in_mrad.user_setpoint.source == "ca://prefix:ROLL.VAL"


@pytest.fixture
async def dcm() -> DoubleCrystalMonochromatorBase:
    async with init_devices(mock=True):
        dcm = DoubleCrystalMonochromatorBase(
            "DCM-01", PitchAndRollCrystal, StationaryCrystal
        )
    return dcm


@pytest.mark.parametrize(
    "energy_kev, energy_ev",
    [
        (0.0, 0.0),
        (1.0, 1000.0),
        (0.102, 102.0),
    ],
)
async def test_ev_to_kev(
    dcm: DoubleCrystalMonochromatorBase,
    energy_kev: float,
    energy_ev: float,
):
    set_mock_value(dcm.energy_in_keV.user_readback, energy_kev)
    await assert_value(dcm.energy_in_eV, energy_ev)
