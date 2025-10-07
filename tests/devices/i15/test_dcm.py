from dodal.devices.common_dcm import RollCrystal, StationaryCrystal
from dodal.devices.i15.dcm import DualCrystalMonoSimple


def test_make_crystals():
    dcm = DualCrystalMonoSimple("prefix:", RollCrystal, StationaryCrystal)
    assert dcm.xtal_1.roll_in_mrad.user_setpoint.source == "ca://prefix:ROLL.VAL"
