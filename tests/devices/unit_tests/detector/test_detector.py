from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from dodal.devices.detector import DetectorParams
from dodal.devices.detector.det_dim_constants import EIGER2_X_16M_SIZE


def create_det_params_with_dir_and_prefix(directory: str | Path, prefix="test"):
    return DetectorParams(
        expected_energy_ev=100,
        exposure_time=1.0,
        directory=directory,  # type: ignore
        prefix=prefix,
        detector_distance=1.0,
        omega_start=0.0,
        omega_increment=0.0,
        num_images_per_trigger=1,
        num_triggers=1,
        use_roi_mode=False,
        det_dist_to_beam_converter_path="tests/devices/unit_tests/test_lookup_table.txt",
        detector_size_constants=EIGER2_X_16M_SIZE,
    )


def test_if_string_provided_check_is_dir(tmp_path: Path):
    assert not (_dir := str(tmp_path)).endswith("/")
    params = create_det_params_with_dir_and_prefix(_dir)
    assert params.directory == str(tmp_path)
    file_path = tmp_path / "foo.h5"
    file_path.touch()
    with pytest.raises(ValidationError):
        create_det_params_with_dir_and_prefix(str(file_path))


def test_if_path_provided_check_is_dir(tmp_path: Path):
    params = create_det_params_with_dir_and_prefix(tmp_path)
    assert params.directory == str(tmp_path)
    file_path = tmp_path / "foo.h5"
    file_path.touch()
    with pytest.raises(ValidationError):
        create_det_params_with_dir_and_prefix(file_path)


@patch(
    "src.dodal.devices.detector.DetectorDistanceToBeamXYConverter.parse_table",
)
def test_correct_det_dist_to_beam_converter_path_passed_in(
    mocked_parse_table, tmp_path: Path
):
    params = DetectorParams(
        expected_energy_ev=100,
        exposure_time=1.0,
        directory=str(tmp_path),
        prefix="test",
        run_number=0,
        detector_distance=1.0,
        omega_start=0.0,
        omega_increment=0.0,
        num_images_per_trigger=1,
        num_triggers=1,
        use_roi_mode=False,
        det_dist_to_beam_converter_path="a fake directory",
        detector_size_constants=EIGER2_X_16M_SIZE,
    )
    assert params.beam_xy_converter.lookup_file == "a fake directory"


@patch(
    "src.dodal.devices.detector.DetectorDistanceToBeamXYConverter.parse_table",
)
def test_run_number_correct_when_not_specified(mocked_parse_table, tmp_path):
    params = DetectorParams(
        expected_energy_ev=100,
        exposure_time=1.0,
        directory=str(tmp_path),
        prefix="test",
        detector_distance=1.0,
        omega_start=0.0,
        omega_increment=0.0,
        num_images_per_trigger=1,
        num_triggers=1,
        use_roi_mode=False,
        det_dist_to_beam_converter_path="a fake directory",
        detector_size_constants=EIGER2_X_16M_SIZE,
    )
    assert params.run_number == 1


@patch(
    "src.dodal.devices.detector.DetectorDistanceToBeamXYConverter.parse_table",
)
def test_run_number_correct_when_specified(mocked_parse_table, tmp_path):
    params = DetectorParams(
        expected_energy_ev=100,
        exposure_time=1.0,
        directory=str(tmp_path),
        run_number=6,
        prefix="test",
        detector_distance=1.0,
        omega_start=0.0,
        omega_increment=0.0,
        num_images_per_trigger=1,
        num_triggers=1,
        use_roi_mode=False,
        det_dist_to_beam_converter_path="a fake directory",
        detector_size_constants=EIGER2_X_16M_SIZE,
    )
    assert params.run_number == 6


def test_detector_params_is_serialisable(tmp_path):
    params = DetectorParams(
        expected_energy_ev=100,
        exposure_time=1.0,
        directory=str(tmp_path),
        prefix="test",
        detector_distance=1.0,
        omega_start=0.0,
        omega_increment=0.0,
        num_images_per_trigger=1,
        num_triggers=1,
        use_roi_mode=False,
        det_dist_to_beam_converter_path="a fake directory",
        detector_size_constants=EIGER2_X_16M_SIZE,
    )
    json = params.model_dump_json()
    assert '"run_number"' not in json
    new_params = DetectorParams.model_validate_json(json)
    assert new_params == params


# Until https://github.com/DiamondLightSource/dodal/issues/775
def test_detector_params_serialisation_unchanged(tmp_path):
    params = DetectorParams(
        expected_energy_ev=100,
        exposure_time=1.0,
        directory=str(tmp_path),
        prefix="test",
        detector_distance=1.0,
        run_number=17,
        omega_start=0.0,
        omega_increment=0.0,
        num_images_per_trigger=1,
        num_triggers=1,
        use_roi_mode=False,
        det_dist_to_beam_converter_path="a fake directory",
        detector_size_constants=EIGER2_X_16M_SIZE,
    )
    json = params.model_dump_json()
    assert params.run_number == 17
    assert '"run_number": 17' in json
    new_params = DetectorParams.model_validate_json(json)
    assert new_params == params


@patch("os.listdir")
def test_prefix_is_used_to_determine_run_number(
    mock_listdir: MagicMock, tmp_path: Path
):
    foos = (f"foo_{i}.nxs" for i in range(4))
    bars = (f"bar_{i}.nxs" for i in range(7))
    bazs = (f"baz_{i}.nxs" for i in range(23, 29))
    files = [*foos, *bars, *bazs]
    mock_listdir.return_value = files

    assert create_det_params_with_dir_and_prefix(tmp_path, "foo").run_number == 4
    assert create_det_params_with_dir_and_prefix(tmp_path, "bar").run_number == 7
    assert create_det_params_with_dir_and_prefix(tmp_path, "baz").run_number == 29
    assert create_det_params_with_dir_and_prefix(tmp_path, "qux").run_number == 1
