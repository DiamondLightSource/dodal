from dodal.devices.common_dcm import StationaryCrystal
from dodal.devices.i15.dcm import DCM


def test_make_crystals():
    dcm = DCM("prefix:", StationaryCrystal, StationaryCrystal)
    assert dcm.xtal_1.roll_in_mrad.user_setpoint.source == "ca://prefix:ROLL.VAL"
