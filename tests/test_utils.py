from unittest.mock import MagicMock, patch

import pytest
from bluesky.protocols import Readable
from ophyd import EpicsMotor
from ophyd.utils import DisconnectedError, ExceptionBundle

from dodal.devices.cryostream import Cryo
from dodal.utils import (
    ExceptionInformation,
    _collect_factories,
    get_hostname,
    make_all_devices,
    make_all_devices_without_throwing,
)


def test_finds_device_factories() -> None:
    import tests.fake_beamline as fake_beamline

    factories = _collect_factories(fake_beamline)

    from tests.fake_beamline import device_a, device_b, device_c

    assert {
        "device_a": device_a,
        "device_b": device_b,
        "device_c": device_c,
    } == factories


def test_makes_devices() -> None:
    import tests.fake_beamline as fake_beamline

    devices = make_all_devices(fake_beamline)
    assert {"readable", "motor", "cryo"} == devices.keys()


def test_makes_devices_with_dependencies() -> None:
    import tests.fake_beamline_dependencies as fake_beamline

    devices = make_all_devices(fake_beamline)
    assert {"readable", "motor", "cryo"} == devices.keys()


def test_makes_devices_with_disordered_dependencies() -> None:
    import tests.fake_beamline_disordered_dependencies as fake_beamline

    devices = make_all_devices(fake_beamline)
    assert {"readable", "motor", "cryo"} == devices.keys()


def test_makes_devices_with_module_name() -> None:
    devices = make_all_devices("tests.fake_beamline")
    assert {"readable", "motor", "cryo"} == devices.keys()


def test_makes_other_devices_when_device_fails() -> None:
    import tests.test_beamline_disordered_and_broken as fake_beamline

    devices = make_all_devices_without_throwing(fake_beamline).devices
    assert "motor" in devices
    assert "readable" not in devices
    assert "cryo" not in devices


def test_dependent_devices_not_instantiated_when_dependency_fails() -> None:
    import tests.test_beamline_disordered_and_broken as fake_beamline

    devices_and_exceptions = make_all_devices_without_throwing(fake_beamline)
    devices = devices_and_exceptions.devices
    exceptions = devices_and_exceptions.exceptions
    assert "cryo" not in devices
    assert "device_x" in exceptions  # root exception
    x_exception = exceptions["device_x"]
    assert isinstance(x_exception, ExceptionInformation)
    assert x_exception.return_type is Readable
    assert isinstance(x_exception.exception, DisconnectedError)
    assert "device_z" in exceptions
    z_exception = exceptions["device_z"]
    assert isinstance(z_exception, ExceptionInformation)
    assert z_exception.return_type is Cryo
    assert isinstance(z_exception.exception, ExceptionBundle)
    assert x_exception.exception in z_exception.exception.exceptions.values()


def test_exception_propagates_if_requested() -> None:
    import tests.test_beamline_disordered_and_broken as fake_beamline

    with pytest.raises(ExceptionBundle):
        make_all_devices(fake_beamline)


def test_get_hostname() -> None:
    with patch("dodal.utils.socket.gethostname") as mock:
        mock.return_value = "a.b.c"
        assert get_hostname() == "a"


def device_a() -> Readable:
    return MagicMock()


def device_b() -> EpicsMotor:
    return MagicMock()
