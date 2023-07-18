import pytest


@pytest.mark.s03
def test_all_i03_devices_connect_to_s03():
    from dodal.beamlines import i03

    i03.set_log_beamline(i03.BL)
    i03.set_utils_beamline(i03.BL)
    from dodal.utils import make_all_devices

    devices = make_all_devices(i03)
    for device in [
        "smargon",
        "zebra",
        "backlight",
        "undulator",
        "aperture_scatterguard",
    ]:
        assert device in devices
