from random import randint

from dodal.beamlines._device_helpers import numbered_slits


def test_slit_field_naming():
    num = randint(1, 20)
    prefix = f"-AL-SLITS-{num:02}:"
    slits = numbered_slits(
        num,
        False,
        True,
    )

    assert slits.name == f"slits_{num}"
    assert slits.x_centre.name == f"slits_{num}-x_centre"
    assert slits.x_gap.name == f"slits_{num}-x_gap"
    assert slits.y_centre.name == f"slits_{num}-y_centre"
    assert slits.y_gap.name == f"slits_{num}-y_gap"
    assert f"{prefix}X:CENTRE.VAL" in slits.x_centre.user_setpoint.source
    assert f"{prefix}X:SIZE.VAL" in slits.x_gap.user_setpoint.source
    assert f"{prefix}Y:CENTRE.VAL" in slits.y_centre.user_setpoint.source
    assert f"{prefix}Y:SIZE.VAL" in slits.y_gap.user_setpoint.source
