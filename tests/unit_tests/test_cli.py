import os
from unittest.mock import patch

import pytest
from click.testing import CliRunner, Result
from ophyd_async.core import Device, NotConnected

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


ALL_SUCCESSFUL_DEVICES: tuple[dict[str, AnyDevice], dict[str, Exception]] = (
    {f"device_{i}": Device() for i in range(6)},
    {},
)

SOME_SUCCESSFUL_DEVICES: tuple[dict[str, AnyDevice], dict[str, Exception]] = (
    {f"device_{i}": Device() for i in range(3)},
    {f"device_{i}": TimeoutError() for i in range(3, 6)},
)

NO_SUCCESSFUL_DEVICES: tuple[dict[str, AnyDevice], dict[str, Exception]] = (
    {},
    {f"device_{i}": TimeoutError() for i in range(6)},
)


def test_cli_sets_beamline_environment_variable(runner: CliRunner):
    with patch.dict(os.environ, clear=True):
        _mock_connect(
            EXAMPLE_BEAMLINE,
            runner=runner,
            devices=ALL_SUCCESSFUL_DEVICES,
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
        devices=ALL_SUCCESSFUL_DEVICES,
    )
    assert "6 devices connected" in result.stdout


@patch.dict(os.environ, clear=True)
def test_cli_connect_in_sim_mode(runner: CliRunner):
    result = _mock_connect(
        "-s",
        EXAMPLE_BEAMLINE,
        runner=runner,
        devices=ALL_SUCCESSFUL_DEVICES,
    )
    assert "6 devices connected (sim mode)" in result.stdout


@patch.dict(os.environ, clear=True)
@pytest.mark.parametrize("devices", [SOME_SUCCESSFUL_DEVICES, NO_SUCCESSFUL_DEVICES])
def test_cli_connect_when_devices_error(
    runner: CliRunner,
    devices: tuple[dict[str, AnyDevice], dict[str, Exception]],
):
    with pytest.raises(NotConnected):
        _mock_connect(
            EXAMPLE_BEAMLINE,
            runner=runner,
            devices=SOME_SUCCESSFUL_DEVICES,
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
