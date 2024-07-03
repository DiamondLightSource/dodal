import subprocess
import sys

from dodal import __version__


def test_cli_version():
    cmd = [sys.executable, "-m", "dodal", "--version"]
    assert subprocess.check_output(cmd).decode().strip() == __version__
