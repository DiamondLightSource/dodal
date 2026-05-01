import os
from unittest.mock import MagicMock, patch

import pytest
from bluesky import RunEngine

from dodal.device_manager import DeviceManager
from dodal.plans.save_panda import _build_panda, _save_panda, main


@pytest.fixture(autouse=True)
def patch_run_engine_in_save_panda_to_avoid_leaks(run_engine: RunEngine):
    with patch("dodal.plans.save_panda.RunEngine", return_value=run_engine):
        yield


def test_build_panda(sim_run_engine):
    panda = MagicMock()
    panda_factory = MagicMock()
    panda_factory.build.return_value = panda

    dev_man = MagicMock(spec=DeviceManager)
    dev_man.__getitem__.side_effect = {"panda": panda_factory}.get

    with patch(
        "dodal.plans.save_panda.importlib.import_module",
        return_value=MagicMock(devices=dev_man),
    ) as imp:
        built_panda = _build_panda("i03", "panda")
        imp.assert_called_once_with("dodal.beamlines.i03")
        panda_factory.build.assert_called_once_with(connect_immediately=True)
        assert built_panda is panda


def test_save_panda(sim_run_engine):
    panda = MagicMock()

    directory = "test"
    filename = "file.yml"
    with (
        patch("dodal.plans.save_panda._build_panda", return_value=panda) as build,
        patch(
            "dodal.plans.save_panda.RunEngine",
            return_value=MagicMock(side_effect=sim_run_engine.simulate_plan),
        ),
        patch("dodal.plans.save_panda.store_settings") as mock_store_settings,
        patch("dodal.plans.save_panda.YamlSettingsProvider") as mock_settings_provider,
    ):
        _save_panda("i03", "panda", directory, filename)

        build.assert_called_once_with("i03", "panda")
        mock_store_settings.assert_called_with(
            mock_settings_provider(),
            "file.yml",
            panda,
        )


@patch(
    "dodal.plans.save_panda.sys.exit",
    side_effect=AssertionError("This exception expected"),
)
def test_save_panda_failure_to_create_device_exits_with_failure_code(mock_exit, tmpdir):
    with patch(
        "dodal.plans.save_panda._build_panda",
        side_effect=ValueError("device does not exist"),
    ):
        with pytest.raises(AssertionError):
            _save_panda("i03", "panda", tmpdir, "filename")

    mock_exit.assert_called_once_with(1)


@patch("dodal.plans.save_panda._save_panda")
@pytest.mark.parametrize(
    "beamline, args, expected_beamline, expected_device_name, expected_output_dir, expected_output_file, "
    "expected_return_value",
    [
        (
            "i03",
            ["--output-file=my_dir/my_file_name"],
            "i03",
            "panda",
            "my_dir",
            "my_file_name",
            0,
        ),
        (
            "i02",
            [
                "--beamline=i04",
                "--output-file=my_dir/my_file_name",
            ],
            "i04",
            "panda",
            "my_dir",
            "my_file_name",
            0,
        ),
        (
            None,
            [
                "--beamline=i04",
                "--output-file=my_dir/my_file_name",
            ],
            "i04",
            "panda",
            "my_dir",
            "my_file_name",
            0,
        ),
        (
            "i03",
            [
                "--device-name=my_panda",
                "--output-file=my_dir/my_file_name",
            ],
            "i03",
            "my_panda",
            "my_dir",
            "my_file_name",
            0,
        ),
        (
            None,
            [
                "--device-name=my_panda",
                "--output-file=my_dir/my_file_name",
            ],
            "i03",
            "my_panda",
            "my_dir",
            "my_file_name",
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
    expected_output_dir,
    expected_output_file,
    expected_return_value,
):
    env_patch = {}
    if beamline:
        env_patch["BEAMLINE"] = beamline

    with patch.dict(os.environ, env_patch):
        return_value = main(args)

    assert return_value == expected_return_value
    if not expected_return_value:
        mock_save_panda.assert_called_with(
            expected_beamline,
            expected_device_name,
            expected_output_dir,
            expected_output_file,
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
@patch("dodal.plans.save_panda._save_panda")
@patch("dodal.plans.save_panda.Path", autospec=True)
def test_file_exists_check(
    mock_path: MagicMock,
    mock_save_panda: MagicMock,
    file_exists: bool,
    force: bool,
    save_panda_called: bool,
    expected_return_value: int,
    tmpdir,
):
    exists = mock_path.return_value.exists
    exists.return_value = file_exists
    argv = [
        "--beamline=i03",
        f"--output-file={tmpdir}/test_output_file.yml",
    ]
    if force:
        argv.insert(1, "--force")

    with patch.dict("os.environ"):
        return_value = main(argv)

    mock_path.assert_called_with(
        f"{mock_path.return_value.parent}/{mock_path.return_value.name}"
    )
    exists.assert_called_once()
    if save_panda_called:
        mock_save_panda.assert_called_with(
            "i03",
            "panda",
            str(mock_path.return_value.parent),
            str(mock_path.return_value.name),
        )
    else:
        mock_save_panda.assert_not_called()

    assert return_value == expected_return_value
