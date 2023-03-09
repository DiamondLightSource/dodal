from unittest.mock import patch

from dodal.utils import collect_factories, get_hostname, make_all_devices


def test_finds_device_factories() -> None:
    import tests.fake_beamline as fake_beamline

    factories = set(collect_factories(fake_beamline))

    from tests.fake_beamline import device_a, device_b, device_c

    assert {device_a, device_b, device_c} == factories


def test_makes_devices() -> None:
    import tests.fake_beamline as fake_beamline

    devices = make_all_devices(fake_beamline)
    assert {"readable", "motor", "cryo"} == devices.keys()


def test_get_hostname() -> None:
    with patch("dodal.utils.socket.gethostname") as mock:
        mock.return_value = "a.b.c"
        assert get_hostname() == "a"
