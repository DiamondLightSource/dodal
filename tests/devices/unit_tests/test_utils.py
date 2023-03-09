from unittest.mock import MagicMock, patch

from bluesky.protocols import Readable
from ophyd import EpicsMotor

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


def test_makes_devices_with_module_name() -> None:
    devices = make_all_devices("tests.fake_beamline")
    assert {"readable", "motor", "cryo"} == devices.keys()


def test_get_hostname() -> None:
    with patch("dodal.utils.socket.gethostname") as mock:
        mock.return_value = "a.b.c"
        assert get_hostname() == "a"


def device_a() -> Readable:
    return MagicMock()


def device_b() -> EpicsMotor:
    return MagicMock()
