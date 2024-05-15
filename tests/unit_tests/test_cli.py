from unittest.mock import patch

import pytest
from click.testing import CliRunner

from dodal import __version__
from dodal.beamlines import all_beamline_names
from dodal.cli import main


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


def test_cli_connect(runner: CliRunner):
    beamline = next(iter(all_beamline_names()))  # Test with an example beamline,
    # device instantiation is already tested in beamline unit tests

    with patch(
        "dodal.cli.make_all_devices",
        return_value={f"device_{i}": object() for i in range(3)},
    ):
        result = runner.invoke(
            main,
            ["connect", beamline],
            catch_exceptions=False,
        )
    assert result.stdout.startswith("3 devices connected")


def test_cli_connect_in_sim_mode(runner: CliRunner):
    beamline = next(iter(all_beamline_names()))  # Test with an example beamline,
    # device instantiation is already tested in beamline unit tests

    with patch(
        "dodal.cli.make_all_devices",
        return_value={f"device_{i}": object() for i in range(3)},
    ):
        result = runner.invoke(
            main,
            ["connect", "-s", beamline],
            catch_exceptions=False,
        )
    assert result.stdout.startswith("3 devices connected (sim mode)")
