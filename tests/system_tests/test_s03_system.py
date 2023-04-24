import pytest


@pytest.mark.s03
def test_all_i03_devices_connect_to_s03():
    from dodal import i03
    from dodal.utils import make_all_devices

    make_all_devices(i03)
