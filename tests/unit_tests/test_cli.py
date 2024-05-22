import os
from unittest.mock import patch

import pytest
from click.testing import CliRunner, Result

from dodal import __version__
from dodal.cli import main

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


def test_cli_sets_beamline_environment_variable(runner: CliRunner):
    with patch.dict(os.environ, clear=True):
        _mock_connect(EXAMPLE_BEAMLINE, runner=runner)
        assert os.environ["BEAMLINE"] == EXAMPLE_BEAMLINE


def test_cli_connect(runner: CliRunner):
    result = _mock_connect(EXAMPLE_BEAMLINE, runner=runner)
    assert result.stdout.startswith("3 devices connected")


def test_cli_connect_in_sim_mode(runner: CliRunner):
    result = _mock_connect("-s", EXAMPLE_BEAMLINE, runner=runner)
    assert result.stdout.startswith("3 devices connected (sim mode)")


def _mock_connect(*args, runner: CliRunner) -> Result:
    with patch(
        "dodal.cli.make_all_devices",
        return_value={f"device_{i}": object() for i in range(3)},
    ):
        result = runner.invoke(
            main,
            ["connect"] + list(args),
            catch_exceptions=False,
        )
    return result
