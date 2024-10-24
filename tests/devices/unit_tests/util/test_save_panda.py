import os
from unittest.mock import MagicMock, patch

import pytest
from bluesky.simulators import RunEngineSimulator
from ophyd_async.fastcs.panda import phase_sorter

from dodal.devices.util.save_panda import _save_panda, main


def test_save_panda():
    sim_run_engine = RunEngineSimulator()
    panda = MagicMock()
    with (
        patch(
            "dodal.devices.util.save_panda.make_device", return_value={"panda": panda}
        ) as mock_make_device,
        patch(
            "dodal.devices.util.save_panda.RunEngine",
            return_value=MagicMock(side_effect=sim_run_engine.simulate_plan),
        ),
        patch("dodal.devices.util.save_panda.save_device") as mock_save_device,
    ):
        _save_panda("i03", "panda", "test/file.yml")

        mock_make_device.assert_called_with("dodal.beamlines.i03", "panda")
        mock_save_device.assert_called_with(panda, "test/file.yml", sorter=phase_sorter)


@patch(
    "dodal.devices.util.save_panda.sys.exit",
    side_effect=AssertionError("This exception expected"),
)
def test_save_panda_failure_to_create_device_exits_with_failure_code(mock_exit):
    with patch(
        "dodal.devices.util.save_panda.make_device",
        side_effect=ValueError("device does not exist"),
    ):
        with pytest.raises(AssertionError):
            _save_panda("i03", "panda", "test/file.yml")

    mock_exit.assert_called_once_with(1)


@patch("dodal.devices.util.save_panda._save_panda")
@pytest.mark.parametrize(
    "beamline, args, expected_beamline, expected_device_name, expected_output_file, "
    "expected_return_value",
    [
        ("i03", ["my_file_name.yml"], "i03", "panda", "my_file_name.yml", 0),
        (
            "i02",
            ["--beamline=i04", "my_file_name.yml"],
            "i04",
            "panda",
            "my_file_name.yml",
            0,
        ),
        (
            None,
            ["--beamline=i04", "my_file_name.yml"],
            "i04",
            "panda",
            "my_file_name.yml",
            0,
        ),
        (
            "i03",
            ["--device-name=my_panda", "my_file_name.yml"],
            "i03",
            "my_panda",
            "my_file_name.yml",
            0,
        ),
        (
            None,
            ["--device-name=my_panda", "my_file_name.yml"],
            "i03",
            "my_panda",
            "my_file_name.yml",
            1,
        ),
    ],
)
def test_main(
    mock_save_panda: MagicMock,
    beamline: str,
    args: list[str],
    expected_beamline,
    expected_device_name,
    expected_output_file,
    expected_return_value,
):
    args.insert(0, "save_panda")
    env_patch = {}
    if beamline:
        env_patch["BEAMLINE"] = beamline

    with patch.dict(os.environ, env_patch):
        return_value = main(args)

    assert return_value == expected_return_value
    if not expected_return_value:
        mock_save_panda.assert_called_with(
            expected_beamline, expected_device_name, expected_output_file
        )


@pytest.mark.parametrize(
    "file_exists, force, save_panda_called, expected_return_value",
    [
        (True, True, True, 0),
        (False, False, True, 0),
        (True, False, False, 1),
        (True, True, True, 0),
    ],
)
@patch("dodal.devices.util.save_panda._save_panda")
@patch("dodal.devices.util.save_panda.Path", autospec=True)
def test_file_exists_check(
    mock_path: MagicMock,
    mock_save_panda: MagicMock,
    file_exists: bool,
    force: bool,
    save_panda_called: bool,
    expected_return_value: int,
):
    exists = mock_path.return_value.exists
    exists.return_value = file_exists
    argv = ["save_panda", "--beamline=i03", "test_output_file.yml"]
    if force:
        argv.insert(1, "--force")

    with patch.dict("os.environ"):
        return_value = main(argv)

    mock_path.assert_called_with("test_output_file.yml")
    exists.assert_called_once()
    if save_panda_called:
        mock_save_panda.assert_called_with("i03", "panda", "test_output_file.yml")
    else:
        mock_save_panda.assert_not_called()

    assert return_value == expected_return_value
