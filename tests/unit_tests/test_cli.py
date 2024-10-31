import os
from collections.abc import Sequence
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner, Result
from ophyd_async.core import Device

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
    result = _mock_connect(
        EXAMPLE_BEAMLINE,
        runner=runner,
        devices=SOME_SUCCESSFUL_DEVICES,
    )
    assert result.exit_code != 0


@pytest.mark.parametrize(
    "args, expected_beamlines",
    [[["ALL"], ["i03"]], [["--include-training", "ALL"], ["i03", "training_rig"]]],
)
@patch(
    "dodal.cli.all_beamline_names", new=MagicMock(return_value=["i03", "training_rig"])
)
@patch.dict(os.environ, clear=True)
def test_cli_all_include_training(
    runner: CliRunner, args: Sequence[str], expected_beamlines: Sequence[str]
):
    result = _mock_connect(*args, runner=runner, devices=ALL_SUCCESSFUL_DEVICES)
    for bl in expected_beamlines:
        assert f"Attempting connection to {bl}" in result.stdout


@pytest.mark.parametrize(
    "args, expected_beamlines",
    [[["ALL"], ["i03"]], [["--include-sim", "ALL"], ["i03", "s03"]]],
)
@patch("dodal.cli.all_beamline_names", new=MagicMock(return_value=["i03", "s03"]))
@patch.dict(os.environ, clear=True)
def test_cli_all_include_sim(
    runner: CliRunner, args: Sequence[str], expected_beamlines: Sequence[str]
):
    result = _mock_connect(*args, runner=runner, devices=ALL_SUCCESSFUL_DEVICES)
    for bl in expected_beamlines:
        assert f"Attempting connection to {bl}" in result.stdout


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
