import os
import subprocess
import sys

import pytest

import dodal.plans.save_panda as save_panda
from dodal import __version__


@pytest.mark.skip_in_pycharm(reason="subprocess returns tty escape sequences")
def test_cli_version():
    cmd = [sys.executable, "-m", "dodal", "--version"]
    assert subprocess.check_output(cmd, timeout=5).decode().strip() == __version__


def test_save_panda_entry_point():
    expected_exit_code = 0
    cmd_str = "save-panda --help"
    assert subprocess.getstatusoutput(cmd_str)[0] == expected_exit_code


def test_save_panda_fails_if_no_arguments_passed():
    expected_exit_code = 2
    assert subprocess.getstatusoutput("save-panda")[0] == expected_exit_code


def test_save_panda_error_if_no_beamline_set():
    expected_exit_code = 1
    cmd_str = "save-panda --output-file somefile"
    res = subprocess.getstatusoutput(cmd_str)
    assert res[0] == expected_exit_code
    assert res[1] == "BEAMLINE not set and --beamline not specified"


def test_can_run_save_panda_outside_entry_point():
    path = os.path.abspath(save_panda.__file__)
    result = subprocess.run(
        [
            sys.executable,
            os.path.basename(path),
            "--help",
        ],
        cwd=os.path.dirname(path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout
