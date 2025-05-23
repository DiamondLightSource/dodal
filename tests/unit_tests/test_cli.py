import os
from unittest.mock import patch

import pytest
from click.testing import CliRunner, Result
from ophyd.device import DEFAULT_CONNECTION_TIMEOUT
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    LazyMock,
    NotConnected,
)

from dodal import __version__
from dodal.cli import main
from dodal.utils import AnyDevice, OphydV1Device, OphydV2Device

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
    ophyd_async_instantiation_failures: int = 0,
    ophyd_async_connection_failures: int = 0,
    ophyd_happy_devices: int = 0,
    ophyd_instantiation_failures: int = 0,
    ophyd_connection_failures: int = 0,
) -> tuple[dict[str, AnyDevice], dict[str, Exception]]:
    devices = {
        **{
            f"ophyd_async_happy_device_{i}": OphydV2Device(
                name=f"ophyd_async_happy_device_{i}"
            )
            for i in range(ophyd_async_happy_devices)
        },
        **{
            f"ophyd_async_unconnectable_device_{i}": UnconnectableOphydAsyncDevice(
                name=f"ophyd_async_unconnectable_device_{i}"
            )
            for i in range(ophyd_async_connection_failures)
        },
        **{
            f"ophyd_happy_device_{i}": OphydV1Device(name=f"ophyd_happy_device_{i}")
            for i in range(ophyd_happy_devices)
        },
        **{
            f"ophyd_unconnectable_device_{i}": UnconnectableOphydDevice(
                name=f"ophyd_unconnectable_device_{i}"
            )
            for i in range(ophyd_connection_failures)
        },
    }
    exceptions: dict[str, Exception] = {
        **{
            f"ophyd_async_failed_device_{i}": TimeoutError()
            for i in range(ophyd_async_instantiation_failures)
        },
        **{
            f"ophyd_failed_device_{i}": TimeoutError()
            for i in range(ophyd_instantiation_failures)
        },
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
        (
            device_results(
                ophyd_async_happy_devices=3,
                ophyd_async_connection_failures=3,
            ),
            3,
        ),
        (
            device_results(
                ophyd_async_happy_devices=3,
                ophyd_async_instantiation_failures=3,
            ),
            3,
        ),
        (
            device_results(
                ophyd_async_happy_devices=2,
                ophyd_async_instantiation_failures=2,
                ophyd_async_connection_failures=2,
            ),
            2,
        ),
        (
            device_results(
                ophyd_async_instantiation_failures=3,
                ophyd_async_connection_failures=3,
            ),
            0,
        ),
        # Ophyd Only
        (device_results(ophyd_happy_devices=6), 6),
        (
            device_results(
                ophyd_happy_devices=3,
                ophyd_connection_failures=3,
            ),
            3,
        ),
        (
            device_results(
                ophyd_happy_devices=3,
                ophyd_instantiation_failures=3,
            ),
            3,
        ),
        (
            device_results(
                ophyd_happy_devices=2,
                ophyd_instantiation_failures=2,
                ophyd_connection_failures=2,
            ),
            2,
        ),
        (
            device_results(
                ophyd_instantiation_failures=3,
                ophyd_connection_failures=3,
            ),
            0,
        ),
        # Mixture
        (
            device_results(
                ophyd_happy_devices=1,
                ophyd_instantiation_failures=1,
                ophyd_connection_failures=1,
                ophyd_async_happy_devices=1,
                ophyd_async_instantiation_failures=1,
                ophyd_async_connection_failures=1,
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
        device_results(
            ophyd_async_connection_failures=6,
        ),
        device_results(
            ophyd_async_instantiation_failures=6,
        ),
        device_results(
            ophyd_async_happy_devices=3,
            ophyd_async_connection_failures=3,
        ),
        device_results(
            ophyd_async_happy_devices=3, ophyd_async_instantiation_failures=3
        ),
        device_results(
            ophyd_async_instantiation_failures=3,
            ophyd_async_connection_failures=3,
        ),
        device_results(
            ophyd_async_happy_devices=2,
            ophyd_async_instantiation_failures=2,
            ophyd_async_connection_failures=2,
        ),
        # Ophyd Only
        device_results(
            ophyd_connection_failures=6,
        ),
        device_results(
            ophyd_instantiation_failures=6,
        ),
        device_results(
            ophyd_happy_devices=3,
            ophyd_connection_failures=3,
        ),
        device_results(ophyd_happy_devices=3, ophyd_async_instantiation_failures=3),
        device_results(
            ophyd_instantiation_failures=3,
            ophyd_connection_failures=3,
        ),
        device_results(
            ophyd_happy_devices=2,
            ophyd_instantiation_failures=2,
            ophyd_connection_failures=2,
        ),
        # Mixture
        device_results(
            ophyd_happy_devices=1,
            ophyd_instantiation_failures=1,
            ophyd_connection_failures=1,
            ophyd_async_happy_devices=1,
            ophyd_async_instantiation_failures=1,
            ophyd_async_connection_failures=1,
        ),
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
