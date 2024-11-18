import os
from unittest.mock import patch

import pytest
from click.testing import CliRunner, Result
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    Device,
    LazyMock,
    NotConnected,
)

from dodal import __version__
from dodal.cli import main
from dodal.utils import AnyDevice

# Test with an example beamline, device instantiation is already tested
# in beamline unit tests
EXAMPLE_BEAMLINE = "i22"


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


class UnconnectableDevice(Device):
    async def connect(
        self,
        mock: bool | LazyMock = False,
        timeout: float = DEFAULT_TIMEOUT,
        force_reconnect: bool = False,
    ) -> None:
        raise RuntimeError(f"{self.name}: fake connection error for tests")


def device_results(
    happy_devices: int = 0,
    instantiation_failures: int = 0,
    connection_failures: int = 0,
) -> tuple[dict[str, AnyDevice], dict[str, Exception]]:
    return {
        **{
            f"happy_device_{i}": Device(name=f"happy_device_{i}")
            for i in range(happy_devices)
        },
        **{
            f"unconnectable_device_{i}": UnconnectableDevice(
                name=f"unconnectable_device_{i}"
            )
            for i in range(connection_failures)
        },
    }, {f"failed_device_{i}": TimeoutError() for i in range(instantiation_failures)}


ALL_CONNECTED_DEVICES = device_results(happy_devices=6)
SOME_FAILED_INSTANTIATION = device_results(happy_devices=3, instantiation_failures=3)
SOME_FAILED_CONNECTION = device_results(happy_devices=3, connection_failures=3)
ALL_FAILED_INSTANTIATION = device_results(instantiation_failures=6)
ALL_FAILED_CONNECTION = device_results(connection_failures=6)
SOME_FAILED_INSTANTIATION_OR_CONNECTION = device_results(
    instantiation_failures=3,
    connection_failures=3,
)
SOME_CONNECTED_AND_VARIOUS_FAILURES = device_results(
    happy_devices=2,
    instantiation_failures=2,
    connection_failures=2,
)


def test_cli_sets_beamline_environment_variable(runner: CliRunner):
    with patch.dict(os.environ, clear=True):
        _mock_connect(
            EXAMPLE_BEAMLINE,
            runner=runner,
            devices=ALL_CONNECTED_DEVICES,
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
        devices=ALL_CONNECTED_DEVICES,
    )
    assert "6 devices connected (sim mode)" in result.stdout


@patch.dict(os.environ, clear=True)
@pytest.mark.parametrize(
    "devices,expected_connections",
    [
        (ALL_CONNECTED_DEVICES, 6),
        (SOME_FAILED_CONNECTION, 3),
        (SOME_FAILED_INSTANTIATION, 3),
        (SOME_CONNECTED_AND_VARIOUS_FAILURES, 2),
        (SOME_FAILED_INSTANTIATION_OR_CONNECTION, 0),
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
        ALL_FAILED_CONNECTION,
        ALL_FAILED_INSTANTIATION,
        SOME_FAILED_CONNECTION,
        SOME_FAILED_INSTANTIATION,
        SOME_FAILED_INSTANTIATION_OR_CONNECTION,
        SOME_CONNECTED_AND_VARIOUS_FAILURES,
    ],
)
def test_cli_connect_when_devices_error(
    runner: CliRunner,
    devices: tuple[dict[str, AnyDevice], dict[str, Exception]],
):
    with pytest.raises(NotConnected):
        _mock_connect(
            EXAMPLE_BEAMLINE,
            runner=runner,
            devices=devices,
        )


def _mock_connect(
    *args,
    runner: CliRunner,
    devices: tuple[dict[str, AnyDevice], dict[str, Exception]] = ({}, {}),
    catch_exceptions: bool = False,
) -> Result:
    with patch(
        "dodal.cli.make_all_devices",
        return_value=devices,
    ):
        result = runner.invoke(
            main,
            ["connect"] + list(args),
            catch_exceptions=catch_exceptions,
        )
    return result
