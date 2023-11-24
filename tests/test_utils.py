import os
from unittest.mock import MagicMock, patch

import pytest
from bluesky.protocols import Readable
from ophyd import EpicsMotor

from dodal.beamlines import i03, i23
from dodal.utils import (
    collect_factories,
    get_beamline_based_on_environment_variable,
    get_hostname,
    make_all_devices,
)


def test_finds_device_factories() -> None:
    import tests.fake_beamline as fake_beamline

    factories = collect_factories(fake_beamline)

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


def test_get_hostname() -> None:
    with patch("dodal.utils.socket.gethostname") as mock:
        mock.return_value = "a.b.c"
        assert get_hostname() == "a"


def test_no_signature_builtins_not_devices() -> None:
    import tests.fake_beamline_misbehaving_builtins as fake_beamline

    devices = make_all_devices(fake_beamline)
    assert not devices


def device_a() -> Readable:
    return MagicMock()


def device_b() -> EpicsMotor:
    return MagicMock()


@pytest.mark.parametrize("bl", ["", "$%^&*", "nonexistent"])
def test_invalid_beamline_variable_causes_get_device_module_to_raise(bl):
    with patch.dict(os.environ, {"BEAMLINE": bl}), pytest.raises(ValueError):
        get_beamline_based_on_environment_variable()


@pytest.mark.parametrize("bl,module", [("i03", i03), ("i23", i23)])
def test_valid_beamline_variable_causes_get_device_module_to_return_module(bl, module):
    with patch.dict(os.environ, {"BEAMLINE": bl}):
        assert get_beamline_based_on_environment_variable() == module
