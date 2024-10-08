import os
from unittest.mock import MagicMock, Mock, patch

import pytest
from bluesky.protocols import Readable
from ophyd import EpicsMotor

from dodal.beamlines import i03, i23
from dodal.common.beamlines.device_factory import DeviceInitializationController
from dodal.utils import (
    _find_next_run_number_from_files,
    collect_factories,
    get_beamline_based_on_environment_variable,
    get_hostname,
    get_run_number,
    is_any_device_factory,
    make_all_devices,
    make_device,
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

    devices, exceptions = make_all_devices(fake_beamline)
    assert {"readable", "motor", "cryo"} == devices.keys() and len(exceptions) == 0


def test_makes_devices_with_dependencies() -> None:
    import tests.fake_beamline_dependencies as fake_beamline

    devices, exceptions = make_all_devices(fake_beamline)
    assert {"readable", "motor", "cryo"} == devices.keys() and len(exceptions) == 0


def test_makes_devices_with_disordered_dependencies() -> None:
    import tests.fake_beamline_disordered_dependencies as fake_beamline

    devices, exceptions = make_all_devices(fake_beamline)
    assert {"readable", "motor", "cryo"} == devices.keys() and len(exceptions) == 0


def test_makes_devices_with_module_name() -> None:
    devices, exceptions = make_all_devices("tests.fake_beamline")
    assert {"readable", "motor", "cryo"} == devices.keys() and len(exceptions) == 0


def test_get_hostname() -> None:
    with patch("dodal.utils.socket.gethostname") as mock:
        mock.return_value = "a.b.c"
        assert get_hostname() == "a"


def test_no_signature_builtins_not_devices() -> None:
    import tests.fake_beamline_misbehaving_builtins as fake_beamline

    devices, exceptions = make_all_devices(fake_beamline)
    assert len(devices) == 0
    assert len(exceptions) == 0


def test_no_devices_when_all_factories_raise_exceptions() -> None:
    import tests.fake_beamline_all_devices_raise_exception as fake_beamline

    devices, exceptions = make_all_devices(fake_beamline)
    assert len(devices) == 0
    assert len(exceptions) == 3 and all(
        isinstance(e, Exception) for e in exceptions.values()
    )


def test_some_devices_when_some_factories_raise_exceptions() -> None:
    import tests.fake_beamline_some_devices_working as fake_beamline

    devices, exceptions = make_all_devices(fake_beamline)
    assert len(devices) == 2
    assert len(exceptions) == 1 and all(
        isinstance(e, Exception) for e in exceptions.values()
    )


def test_make_device_with_dependency():
    import tests.fake_beamline_dependencies as fake_beamline

    devices = make_device(fake_beamline, "device_z")
    assert devices.keys() == {"device_x", "device_y", "device_z"}


def test_make_device_no_dependency():
    import tests.fake_beamline_dependencies as fake_beamline

    devices = make_device(fake_beamline, "device_x")
    assert devices.keys() == {"device_x"}


def test_make_device_with_exception():
    import tests.fake_beamline_all_devices_raise_exception as fake_beamline

    with pytest.raises(ValueError):
        make_device(fake_beamline, "device_c")


def test_make_device_with_module_name():
    devices = make_device("tests.fake_beamline", "device_a")
    assert {"device_a"} == devices.keys()


def test_make_device_no_factory():
    import tests.fake_beamline_dependencies as fake_beamline

    with pytest.raises(ValueError):
        make_device(fake_beamline, "this_device_does_not_exist")


def test_make_device_dependency_throws():
    import tests.fake_beamline_broken_dependency as fake_beamline

    with pytest.raises(RuntimeError):
        make_device(fake_beamline, "device_z")


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


def test_find_next_run_number_from_files_gets_correct_number():
    assert (
        _find_next_run_number_from_files(
            ["V31-1-x0093_1.nxs", "V31-1-x0093_2.nxs", "V31-1-x0093_265.nxs"]
        )
        == 266
    )


@patch("dodal.log.LOGGER.warning")
def test_find_next_run_number_gives_warning_with_wrong_nexus_names(
    mock_logger: MagicMock,
):
    assert (
        _find_next_run_number_from_files(
            ["V31-1-x0093.nxs", "eggs", "V31-1-x0093_1.nxs"]
        )
        == 2
    )
    assert mock_logger.call_count == 2


@patch("os.listdir")
@patch("dodal.utils._find_next_run_number_from_files")
def test_get_run_number_finds_all_nexus_files(
    mock_find_next_run_number: MagicMock, mock_list_dir: MagicMock
):
    files = ["blah.nxs", "foo", "bar.nxs", "ham.h5"]
    mock_list_dir.return_value = files
    get_run_number("dir")
    mock_find_next_run_number.assert_called_once_with(["blah.nxs", "bar.nxs"])


@patch("os.listdir")
def test_if_nexus_files_are_unnumbered_then_return_one(
    mock_list_dir: MagicMock,
):
    assert _find_next_run_number_from_files(["file.nxs", "foo.nxs", "ham.nxs"]) == 1


@patch("os.listdir")
@patch("dodal.utils._find_next_run_number_from_files")
def test_run_number_1_given_on_first_nexus_file(
    mock_find_next_run_number: MagicMock, mock_list_dir: MagicMock
):
    files = ["blah", "foo", "bar"]
    mock_list_dir.return_value = files
    assert get_run_number("dir") == 1
    mock_find_next_run_number.assert_not_called()


@patch("os.listdir")
def test_get_run_number_uses_prefix(mock_list_dir: MagicMock):
    foos = (f"foo_{i}.nxs" for i in range(4))
    bars = (f"bar_{i}.nxs" for i in range(7))
    bazs = (f"baz_{i}.nxs" for i in range(23, 29))
    files = [*foos, *bars, *bazs]
    mock_list_dir.return_value = files
    assert get_run_number("dir", "foo") == 4
    assert get_run_number("dir", "bar") == 7
    assert get_run_number("dir", "baz") == 29
    assert get_run_number("dir", "qux") == 1


def test_is_any_device_factory_v1():
    # Mock a function with return annotation corresponding to V1DeviceFactory
    mock_func = Mock()
    mock_func.return_annotation = "V1DeviceType"

    # Mock is_v1_device_type to return True
    with patch("dodal.utils.is_v1_device_type", return_value=True):
        assert is_any_device_factory(mock_func) is True


def test_is_any_device_factory_v2():
    # Mock a function with return annotation corresponding to V2DeviceFactory
    mock_func = Mock()
    mock_func.return_annotation = "V2DeviceType"

    # Mock is_v2_device_type to return True
    with patch("dodal.utils.is_v2_device_type", return_value=True):
        assert is_any_device_factory(mock_func) is True


def test_is_any_device_factory_new():
    # Mock a function instance of DeviceInitializationController
    mock_func = Mock(spec=DeviceInitializationController)
    assert is_any_device_factory(mock_func) is True


def test_is_any_device_factory_invalid():
    # Mock a function with an unsupported return annotation
    mock_func = Mock()
    mock_func.return_annotation = None

    # Mock all is_v1, is_v2, and is_new checks to return False
    with (
        patch("dodal.utils.is_v1_device_factory", return_value=False),
        patch("dodal.utils.is_v2_device_factory", return_value=False),
        patch("dodal.utils.is_new_device_factory", return_value=False),
    ):
        assert is_any_device_factory(mock_func) is False


def test_is_any_device_factory_signature_value_error():
    # Mock a function that raises a ValueError when checking the signature
    mock_func = Mock()

    with patch("dodal.utils.signature", side_effect=ValueError):
        assert is_any_device_factory(mock_func) is False


def test_is_any_device_factory_type_error_new_factory():
    # Mock a function that raises a ValueError when checked with isinstance
    mock_func = Mock()

    # Mock new factory check to raise ValueError
    with patch(
        "dodal.common.beamlines.device_factory.DeviceInitializationController",
        side_effect=ValueError,
    ):
        assert is_any_device_factory(mock_func) is False
