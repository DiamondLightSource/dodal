from dodal.devices.common_dcm import BaseDCM, RollCrystal, StationaryCrystal


def test_make_crystals():
    dcm = BaseDCM("prefix:", RollCrystal, RollCrystal)
    assert dcm.xtal_1.roll_in_mrad.user_setpoint.source == "ca://prefix:XTAL1:ROLL.VAL"
    dcm = BaseDCM("prefix:", RollCrystal, StationaryCrystal)
    assert dcm.xtal_1.roll_in_mrad.user_setpoint.source == "ca://prefix:ROLL.VAL"
