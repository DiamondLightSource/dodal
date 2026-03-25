import os
from unittest.mock import Mock, patch

import pytest
from bluesky import RunEngine
from click.testing import CliRunner, Result
from ophyd.device import DEFAULT_CONNECTION_TIMEOUT
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    LazyMock,
    NotConnectedError,
)

from dodal import __version__
from dodal.cli import main
from dodal.device_manager import DeviceManager
from dodal.utils import AnyDevice, OphydV1Device, OphydV2Device

# Test with an example beamline, device instantiation is already tested
# in beamline unit tests
EXAMPLE_BEAMLINE = "i22"


@pytest.fixture(autouse=True)
def patch_run_engine_in_cli_to_avoid_leaks(run_engine: RunEngine):
    with patch("dodal.cli.RunEngine", return_value=run_engine):
        yield


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_version(runner: CliRunner):
    result = runner.invoke(
        main,
        ["--version"],
        catch_exceptions=False,
    )

    assert result.stdout == f"{__version__}\n"


class UnconnectableOphydDevice(OphydV1Device):
    def wait_for_connection(
        self,
        all_signals: bool = False,
        timeout=DEFAULT_CONNECTION_TIMEOUT,
    ) -> None:
        raise RuntimeError(f"{self.name}: fake connection error for tests")


class UnconnectableOphydAsyncDevice(OphydV2Device):
    async def connect(
        self,
        mock: bool | LazyMock = False,
        timeout: float = DEFAULT_TIMEOUT,
        force_reconnect: bool = False,
    ) -> None:
        raise RuntimeError(f"{self.name}: fake connection error for tests")


def device_results(
    ophyd_async_happy_devices: int = 0,
    ophyd_async_failures: int = 0,
    ophyd_happy_devices: int = 0,
    ophyd_failures: int = 0,
) -> tuple[dict[str, AnyDevice], dict[str, Exception]]:
    devices = {
        **{
            f"ophyd_async_happy_device_{i}": OphydV2Device(
                name=f"ophyd_async_happy_device_{i}"
            )
            for i in range(ophyd_async_happy_devices)
        },
        **{
            f"ophyd_happy_device_{i}": OphydV1Device(name=f"ophyd_happy_device_{i}")
            for i in range(ophyd_happy_devices)
        },
    }
    exceptions: dict[str, Exception] = {
        **{
            f"ophyd_async_failed_device_{i}": TimeoutError()
            for i in range(ophyd_async_failures)
        },
        **{f"ophyd_failed_device_{i}": TimeoutError() for i in range(ophyd_failures)},
    }
    return devices, exceptions


def test_cli_sets_beamline_environment_variable(runner: CliRunner):
    with patch.dict(os.environ, clear=True):
        _mock_connect(
            EXAMPLE_BEAMLINE,
            runner=runner,
            devices=device_results(ophyd_async_happy_devices=6),
        )
        assert os.environ["BEAMLINE"] == EXAMPLE_BEAMLINE


#
# We need to mock the environment because the CLI edits it and this could break other
# tests
#


@patch.dict(os.environ, clear=True)
def test_cli_connect_in_sim_mode(runner: CliRunner):
    result = _mock_connect(
        "-s",
        EXAMPLE_BEAMLINE,
        runner=runner,
        devices=device_results(ophyd_async_happy_devices=6),
    )
    assert "6 devices connected (sim mode)" in result.stdout


@patch.dict(os.environ, clear=True)
@pytest.mark.parametrize(
    "devices,expected_connections",
    [
        # Ophyd-Async Only
        (device_results(ophyd_async_happy_devices=6), 6),
        (device_results(ophyd_async_happy_devices=3, ophyd_async_failures=3), 3),
        (device_results(ophyd_async_happy_devices=2, ophyd_async_failures=2), 2),
        (device_results(ophyd_async_failures=3), 0),
        # Ophyd Only
        (device_results(ophyd_happy_devices=6), 6),
        (device_results(ophyd_happy_devices=3, ophyd_failures=3), 3),
        (device_results(ophyd_happy_devices=2, ophyd_failures=2), 2),
        (device_results(ophyd_failures=3), 0),
        # Mixture
        (
            device_results(
                ophyd_happy_devices=1,
                ophyd_failures=1,
                ophyd_async_happy_devices=1,
                ophyd_async_failures=1,
            ),
            2,
        ),
    ],
)
def test_cli_connect_reports_correct_number_of_connected_devices(
    runner: CliRunner,
    devices: tuple[dict[str, AnyDevice], dict[str, Exception]],
    expected_connections: int,
):
    result = _mock_connect(
        EXAMPLE_BEAMLINE,
        runner=runner,
        devices=devices,
        catch_exceptions=True,
    )
    assert f"{expected_connections} devices connected" in result.stdout


@patch.dict(os.environ, clear=True)
@pytest.mark.parametrize(
    "devices",
    [
        # Ophyd-Async Only
        device_results(ophyd_async_failures=6),
        device_results(ophyd_async_happy_devices=3, ophyd_async_failures=3),
        device_results(ophyd_async_failures=3),
        device_results(ophyd_async_happy_devices=2, ophyd_async_failures=2),
        # Ophyd Only
        device_results(ophyd_failures=6),
        device_results(ophyd_happy_devices=3, ophyd_failures=3),
        device_results(ophyd_failures=3),
        device_results(ophyd_happy_devices=2, ophyd_failures=2),
        # Mixture
        device_results(
            ophyd_happy_devices=1,
            ophyd_failures=1,
            ophyd_async_happy_devices=1,
            ophyd_async_failures=1,
        ),
    ],
)
def test_cli_connect_when_devices_error(
    runner: CliRunner,
    devices: tuple[dict[str, AnyDevice], dict[str, Exception]],
):
    with pytest.raises(NotConnectedError):
        _mock_connect(
            EXAMPLE_BEAMLINE,
            runner=runner,
            devices=devices,
        )


@patch("dodal.cli.importlib")
@patch("dodal.cli.make_all_devices")
@patch("dodal.cli._connect_devices")
@patch.dict(os.environ, clear=True)
def test_missing_device_manager(connect, make, imp, runner: CliRunner):
    # If the device manager cannot be found, it should fall back to the
    # make_all_devices + _connect_devices approach.
    make.return_value = ({}, {})
    runner.invoke(main, ["connect", "-n", "devices", "i22"])
    make.assert_called_once()
    connect.assert_called_once()


@patch.dict(os.environ, clear=True)
@pytest.mark.parametrize("mock", [True, False], ids=["live", "sim"].__getitem__)
def test_device_manager_init(runner: CliRunner, mock: bool):
    with patch("dodal.cli.importlib") as mock_import:
        dm = mock_import.import_module("dodal.beamlines.i22")
        dm.devices = Mock(spec=DeviceManager)
        mock_import.reset_mock()
        runner.invoke(
            main, ["connect", "-n", "devices", "i22"] + (["-s"] if mock else [])
        )
        mock_import.import_module.assert_called_once_with("dodal.beamlines.i22")
        dm.devices.build_and_connect.assert_called_once_with(mock=mock)


def _mock_connect(
    *args,
    runner: CliRunner,
    devices: tuple[dict[str, AnyDevice], dict[str, Exception]] = ({}, {}),
    catch_exceptions: bool = False,
) -> Result:
    with patch(
        "dodal.cli.DeviceManager.build_and_connect",
        return_value=(*devices, {}),
    ):
        result = runner.invoke(
            main,
            ["connect"] + list(args),
            catch_exceptions=catch_exceptions,
        )
    return result


@patch("dodal.cli.importlib")
@patch.dict(os.environ, clear=True)
def test_cli_describe_prints_warning_on_no_device_manager(imp, runner: CliRunner):
    result = runner.invoke(main, ["describe", "-n", "devices", "i22"])
    assert len(result.stdout.split("\n")) == 3
    assert "No device manager" in result.stdout


def _describe_devices(runner, device_docstrings):
    with patch("dodal.cli.importlib") as mock_import:
        dm = mock_import.import_module("dodal.beamlines.i22")
        dm.devices = Mock(spec=DeviceManager)

        devices = {}

        for device_name, docstring in device_docstrings.items():
            mocked_device = Mock()
            mocked_device.__doc__ = docstring
            devices[device_name] = mocked_device

        dm.devices.get_all_factories.return_value = devices
        return runner.invoke(main, ["describe", "-n", "devices", "i22"])


@patch.dict(os.environ, clear=True)
def test_cli_describe_prints_expected_for_one_device(runner: CliRunner):
    result = _describe_devices(runner, {"test_device": "doc_string"})
    assert len(result.stdout.split()) == 7
    assert "test_device" in result.stdout
    assert "doc_string" in result.stdout


@patch.dict(os.environ, clear=True)
def test_cli_describe_prints_expected_for_many_devices(runner: CliRunner):
    result = _describe_devices(
        runner,
        {
            "test_device": "doc_string",
            "test_other": "different_doc",
            "final_test": "final_doc",
        },
    )
    assert len(result.stdout.split()) == 13
    assert "test_other" in result.stdout
    assert "final_doc" in result.stdout
