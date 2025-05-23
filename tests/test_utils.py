import os
from collections.abc import Iterable, Mapping
from shutil import copytree
from typing import Any, cast
from unittest.mock import ANY, MagicMock, Mock, patch

import pytest
from bluesky.protocols import Readable
from bluesky.run_engine import RunEngine
from ophyd_async.epics.motor import Motor

from dodal.beamlines import i03, i23
from dodal.devices.diamond_filter import DiamondFilter, I03Filters
from dodal.utils import (
    AnyDevice,
    OphydV1Device,
    OphydV2Device,
    _find_next_run_number_from_files,
    collect_factories,
    filter_ophyd_devices,
    get_beamline_based_on_environment_variable,
    get_hostname,
    get_run_number,
    is_v2_device_type,
    make_all_devices,
    make_device,
)

# Duplicated here because of top-level import issues
MOCK_DAQ_CONFIG_PATH = "tests/devices/unit_tests/test_daq_configuration"


@pytest.fixture()
def alternate_config(tmp_path) -> str:
    """
    Alternate config dir as MOCK_DAQ_CONFIG_PATH replaces i03.DAQ_CONFIGURATION_PATH
    in conftest.py
    """
    alt_config_path = tmp_path / "alt_daq_configuration"
    copytree(MOCK_DAQ_CONFIG_PATH, alt_config_path)
    return str(alt_config_path)


@pytest.fixture()
def fake_device_factory_beamline():
    import tests.fake_device_factory_beamline as beamline

    factories = [
        f
        for f in collect_factories(beamline, include_skipped=True).values()
        if hasattr(f, "cache_clear")
    ]
    yield beamline
    for f in factories:
        f.cache_clear()  # type: ignore


def test_finds_device_factories() -> None:
    import tests.fake_beamline as fake_beamline

    factories = collect_factories(fake_beamline)

    from tests.fake_beamline import (
        device_a,
        device_b,
        device_c,
        generic_device_d,
        plain_ophyd_v2_device,
    )

    assert {
        "device_a": device_a,
        "device_b": device_b,
        "device_c": device_c,
        "plain_ophyd_v2_device": plain_ophyd_v2_device,
        "generic_device_d": generic_device_d,
    } == factories


def test_makes_devices() -> None:
    import tests.fake_beamline as fake_beamline

    devices, exceptions = make_all_devices(fake_beamline)
    assert {
        "readable",
        "motor",
        "cryo",
        "diamond_filter",
        "ophyd_v2_device",
    } == devices.keys() and len(exceptions) == 0


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
    assert {
        "readable",
        "motor",
        "cryo",
        "diamond_filter",
        "ophyd_v2_device",
    } == devices.keys() and len(exceptions) == 0


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


def test_device_factory_skips(fake_device_factory_beamline):
    devices, exceptions = make_all_devices(fake_device_factory_beamline)
    assert len(devices) == 0
    assert len(exceptions) == 0


def test_device_factory_can_ignore_skip(fake_device_factory_beamline):
    devices, exceptions = make_all_devices(
        fake_device_factory_beamline, include_skipped=True
    )
    assert len(devices) == 4
    assert len(exceptions) == 0


def test_device_factory_can_construct_ophyd_v1_devices(fake_device_factory_beamline):
    device = fake_device_factory_beamline.ophyd_v1_device(
        connect_immediately=True, mock=True, connection_timeout=4.5
    )

    device.wait_for_connection.assert_called_once_with(timeout=4.5)  # type: ignore


def test_device_factory_passes_kwargs_to_wrapped_factory_v1(
    fake_device_factory_beamline,
):
    device = fake_device_factory_beamline.ophyd_v1_device(
        connect_immediately=True,
        mock=True,
        my_int_kwarg=123,
        my_str_kwarg="abc",
        my_float_kwarg=1.23,
    )

    assert device.my_kwargs == {
        "my_int_kwarg": 123,
        "my_str_kwarg": "abc",
        "my_float_kwarg": 1.23,
    }


def test_device_factory_passes_kwargs_to_wrapped_factory_v2(
    RE: RunEngine, fake_device_factory_beamline
):
    device = fake_device_factory_beamline.mock_device(
        connect_immediately=True,
        mock=True,
        my_int_kwarg=123,
        my_str_kwarg="abc",
        my_float_kwarg=1.23,
    )

    assert device.my_kwargs == {  # type: ignore
        "my_int_kwarg": 123,
        "my_str_kwarg": "abc",
        "my_float_kwarg": 1.23,
    }


def test_fake_with_ophyd_sim_passed_to_device_factory(
    RE: RunEngine, fake_device_factory_beamline
):
    fake_device_factory_beamline.mock_device.cache_clear()

    devices, exceptions = make_all_devices(
        fake_device_factory_beamline,
        include_skipped=True,
        fake_with_ophyd_sim=True,
        connect_immediately=True,
    )
    if "mock_device" in exceptions:
        raise exceptions["mock_device"]
    mock_device = cast(Mock, devices["mock_device"])
    mock_device.connect.assert_called_once_with(timeout=ANY, mock=True)


def test_mock_passed_to_device_factory(RE: RunEngine, fake_device_factory_beamline):
    fake_device_factory_beamline.mock_device.cache_clear()

    devices, exceptions = make_all_devices(
        fake_device_factory_beamline,
        include_skipped=True,
        mock=True,
        connect_immediately=True,
    )
    if "mock_device" in exceptions:
        raise exceptions["mock_device"]
    mock_device = cast(Mock, devices["mock_device"])
    mock_device.connect.assert_called_once_with(timeout=ANY, mock=True)


def test_connect_immediately_passed_to_device_factory(
    RE: RunEngine, fake_device_factory_beamline
):
    fake_device_factory_beamline.mock_device.cache_clear()

    devices, exceptions = make_all_devices(
        fake_device_factory_beamline,
        include_skipped=True,
        connect_immediately=False,
    )
    if "mock_device" in exceptions:
        raise exceptions["mock_device"]
    mock_device = cast(Mock, devices["mock_device"])
    mock_device.connect.assert_not_called()


def test_device_factory_can_rename(RE, fake_device_factory_beamline):
    cryo = fake_device_factory_beamline.device_c(mock=True, connect_immediately=True)
    assert cryo.name == "device_c"
    assert cryo.fine.name == "device_c-fine"

    cryo_2 = fake_device_factory_beamline.device_c(name="cryo")
    assert cryo is cryo_2
    assert cryo_2.name == "cryo"
    assert cryo_2.fine.name == "cryo-fine"


def device_a() -> Readable:
    return MagicMock()


def device_b() -> Motor:
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


OPHYD_DEVICE_A = OphydV1Device(prefix="FOO", name="OPHYD_DEVICE_A")
OPHYD_DEVICE_B = OphydV1Device(prefix="BAR", name="OPHYD_DEVICE_B")

OPHYD_ASYNC_DEVICE_A = OphydV2Device(name="OPHYD_ASYNC_DEVICE_A")
OPHYD_ASYNC_DEVICE_B = OphydV2Device(name="OPHYD_ASYNC_DEVICE_B")


def _filtering_test_cases() -> Iterable[
    tuple[
        Mapping[str, AnyDevice],
        Mapping[str, OphydV1Device],
        Mapping[str, OphydV2Device],
    ]
]:
    yield {}, {}, {}
    yield (
        {"oa": OPHYD_DEVICE_A},
        {"oa": OPHYD_DEVICE_A},
        {},
    )
    yield (
        {"aa": OPHYD_ASYNC_DEVICE_A},
        {},
        {"aa": OPHYD_ASYNC_DEVICE_A},
    )
    yield (
        {"oa": OPHYD_DEVICE_A, "ob": OPHYD_DEVICE_B},
        {"oa": OPHYD_DEVICE_A, "ob": OPHYD_DEVICE_B},
        {},
    )
    yield (
        {
            "aa": OPHYD_ASYNC_DEVICE_A,
            "ab": OPHYD_ASYNC_DEVICE_B,
        },
        {},
        {
            "aa": OPHYD_ASYNC_DEVICE_A,
            "ab": OPHYD_ASYNC_DEVICE_B,
        },
    )
    yield (
        {
            "oa": OPHYD_DEVICE_A,
            "aa": OPHYD_ASYNC_DEVICE_A,
        },
        {"oa": OPHYD_DEVICE_A},
        {"aa": OPHYD_ASYNC_DEVICE_A},
    )
    yield (
        {
            "oa": OPHYD_DEVICE_A,
            "aa": OPHYD_ASYNC_DEVICE_A,
            "ob": OPHYD_DEVICE_B,
            "ab": OPHYD_ASYNC_DEVICE_B,
        },
        {"oa": OPHYD_DEVICE_A, "ob": OPHYD_DEVICE_B},
        {
            "aa": OPHYD_ASYNC_DEVICE_A,
            "ab": OPHYD_ASYNC_DEVICE_B,
        },
    )


@pytest.mark.parametrize(
    "all_devices,expected_ophyd_devices,expected_ophyd_async_devices",
    list(_filtering_test_cases()),
)
def test_filter_ophyd_devices_filters_ophyd_devices(
    all_devices: Mapping[str, AnyDevice],
    expected_ophyd_devices: Mapping[str, OphydV1Device],
    expected_ophyd_async_devices: Mapping[str, OphydV2Device],
):
    ophyd_devices, ophyd_async_devices = filter_ophyd_devices(all_devices)
    assert ophyd_devices == expected_ophyd_devices
    assert ophyd_async_devices == expected_ophyd_async_devices


def test_filter_ophyd_devices_raises_for_extra_types():
    with pytest.raises(ValueError):
        ophyd_devices, ophyd_async_devices = filter_ophyd_devices(
            {
                "oa": OphydV1Device(prefix="", name="oa"),
                "aa": OphydV2Device(name="aa"),
                "ab": 3,  # type: ignore
            }
        )


@pytest.mark.parametrize(
    "input, expected_result",
    [
        [Readable, False],
        [OphydV1Device, False],
        [OphydV2Device, True],
        [DiamondFilter[I03Filters], True],
        [None, False],
        [1, False],
    ],
)
def test_is_v2_device_type(input: Any, expected_result: bool):
    assert is_v2_device_type(input) == expected_result


def test_calling_factory_with_different_args_raises_an_exception():
    i03.undulator(daq_configuration_path=MOCK_DAQ_CONFIG_PATH)
    with pytest.raises(
        RuntimeError,
        match="Device factory method called multiple times with different parameters",
    ):
        i03.undulator(daq_configuration_path=MOCK_DAQ_CONFIG_PATH + "x")
    i03.undulator.cache_clear()


def test_calling_factory_with_different_args_does_not_raise_an_exception_after_cache_clear(
    alternate_config,
):
    i03.undulator(daq_configuration_path=MOCK_DAQ_CONFIG_PATH)
    i03.undulator.cache_clear()
    i03.undulator(daq_configuration_path=alternate_config)
    i03.undulator.cache_clear()


def test_factories_can_be_called_in_any_order(alternate_config):
    i03.undulator_dcm(daq_configuration_path=alternate_config)
    i03.undulator(daq_configuration_path=alternate_config)

    i03.undulator_dcm.cache_clear()
    i03.undulator.cache_clear()

    i03.undulator(daq_configuration_path=alternate_config)
    i03.undulator_dcm(daq_configuration_path=alternate_config)

    i03.undulator.cache_clear()
    i03.undulator_dcm.cache_clear()


def test_factory_calls_are_cached(alternate_config):
    undulator1 = i03.undulator(daq_configuration_path=alternate_config)
    undulator2 = i03.undulator(daq_configuration_path=alternate_config)
    assert undulator1 is undulator2
    i03.undulator.cache_clear()
