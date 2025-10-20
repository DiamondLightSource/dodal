import pytest
from ophyd_async.core import init_devices

from dodal.devices.common_dcm import RollCrystal, StationaryCrystal
from dodal.devices.i15.dcm import BaseDCMforI15


@pytest.fixture
def dcm() -> BaseDCMforI15[RollCrystal, StationaryCrystal]:
    with init_devices(mock=True):
        dcm = BaseDCMforI15("prefix:", RollCrystal, StationaryCrystal)
    return dcm


def test_dcm_make_crystals(dcm: BaseDCMforI15[RollCrystal, StationaryCrystal]) -> None:
    assert dcm.xtal_1.roll_in_mrad.user_setpoint.source == "mock+ca://prefix:ROLL.VAL"
