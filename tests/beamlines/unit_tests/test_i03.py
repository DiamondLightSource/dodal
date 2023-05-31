from dodal.beamlines import beamline_utils, i03
from dodal.devices.aperturescatterguard import AperturePositions, ApertureScatterguard
from dodal.utils import make_all_devices


def test_list():
    beamline_utils.clear_devices()
    i03.zebra(wait_for_connection=False)
    i03.synchrotron(wait_for_connection=False)
    i03.aperture_scatterguard(wait_for_connection=False)
    assert beamline_utils.list_active_devices() == [
        "zebra",
        "synchrotron",
        "aperture_scatterguard",
    ]


def test_device_creation():
    beamline_utils.clear_devices()
    devices = make_all_devices(i03, fake_with_ophyd_sim=True)
    for device_name in devices.keys():
        assert device_name in beamline_utils.ACTIVE_DEVICES
    assert len(beamline_utils.ACTIVE_DEVICES) == len(devices)


def test_devices_are_identical():
    beamline_utils.clear_devices()
    devices_a = make_all_devices(i03, fake_with_ophyd_sim=True)
    devices_b = make_all_devices(i03, fake_with_ophyd_sim=True)
    for device_name in devices_a.keys():
        assert devices_a[device_name] is devices_b[device_name]


def test_getting_second_aperture_scatterguard_gives_valid_device():
    beamline_utils.clear_devices()
    test_positions = AperturePositions(
        (0, 1, 2, 3, 4), (5, 6, 7, 8, 9), (10, 11, 12, 13, 14), (15, 16, 17, 18, 19)
    )
    ap_sg: ApertureScatterguard = i03.aperture_scatterguard(
        fake_with_ophyd_sim=True, aperture_positions=test_positions
    )
    assert ap_sg.aperture_positions is not None
    ap_sg = i03.aperture_scatterguard(fake_with_ophyd_sim=True)
    assert ap_sg.aperture_positions is not None
