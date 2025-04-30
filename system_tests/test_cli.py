import pytest
from click.testing import CliRunner

from dodal import __version__
from dodal.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_cli_version(runner: CliRunner):
    response = runner.invoke(main, "--version")
    assert response.exit_code == 0
    assert response.output.strip() == __version__
