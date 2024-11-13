import os
from unittest.mock import patch

import pytest
from click.testing import CliRunner, Result
from ophyd_async.core import DEFAULT_TIMEOUT, Device, LazyMock, NotConnected

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
    happy_devices: int,
    instantiation_failures: int = 0,
    connection_failures: int = 0,
) -> tuple[dict[str, AnyDevice], dict[str, Exception]]:
    happy = {f"happy_device_{i}": Device() for i in range(happy_devices)}
    conn = {
        f"unconnectable_device_{i}": UnconnectableDevice()
        for i in range(connection_failures)
    }
    failed_devices: dict[str, Exception] = {
        f"failed_device_{i}": TimeoutError() for i in range(instantiation_failures)
    }

    return {**happy, **conn}, failed_devices


ALL_CONNECTED_DEVICES: tuple[dict[str, AnyDevice], dict[str, Exception]] = (
    {f"device_{i}": Device(name=f"device_{i}") for i in range(6)},
    {},
)

SOME_FAILED_INSTANTIATION: tuple[dict[str, AnyDevice], dict[str, Exception]] = (
    {f"device_{i}": Device(name=f"device_{i}") for i in range(3)},
    {f"device_{i}": TimeoutError() for i in range(3, 6)},
)


SOME_FAILED_CONNECTION: tuple[dict[str, AnyDevice], dict[str, Exception]] = (
    {
        **{f"device_{i}": Device(name=f"device_{i}") for i in range(3)},
        **{f"device_{i}": UnconnectableDevice(name=f"device_{i}") for i in range(3, 6)},
    },
    {},
)

ALL_FAILED_INSTANTIATION: tuple[dict[str, AnyDevice], dict[str, Exception]] = (
    {},
    {f"device_{i}": TimeoutError() for i in range(6)},
)

ALL_FAILED_CONNECTION: tuple[dict[str, AnyDevice], dict[str, Exception]] = (
    {f"device_{i}": UnconnectableDevice(name=f"device_{i}") for i in range(6)},
    {},
)


SOME_FAILED_INSTANTIATION_OR_CONNECTION: tuple[
    dict[str, AnyDevice], dict[str, Exception]
] = (
    {
        **{f"device_{i}": Device(name=f"device_{i}") for i in range(1)},
        **{f"device_{i}": UnconnectableDevice(name=f"device_{i}") for i in range(2, 3)},
    },
    {f"device_{i}": TimeoutError() for i in range(3, 6)},
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
def test_cli_connect(runner: CliRunner):
    result = _mock_connect(
        EXAMPLE_BEAMLINE,
        runner=runner,
        devices=ALL_CONNECTED_DEVICES,
    )
    assert "6 devices connected" in result.stdout


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
    "devices",
    [
        ALL_FAILED_CONNECTION,
        ALL_FAILED_INSTANTIATION,
        SOME_FAILED_CONNECTION,
        SOME_FAILED_INSTANTIATION,
        SOME_FAILED_INSTANTIATION_OR_CONNECTION,
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
) -> Result:
    with patch(
        "dodal.cli.make_all_devices",
        return_value=devices,
    ):
        result = runner.invoke(
            main,
            ["connect"] + list(args),
            catch_exceptions=False,
        )
    return result
