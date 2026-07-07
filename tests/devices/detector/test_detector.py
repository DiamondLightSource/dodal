from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from dodal.devices.detector import DetectorParams
from dodal.devices.detector.det_dim_constants import EIGER2_X_16M_SIZE
from tests.devices.test_data import TEST_LUT_TXT


def create_det_params_with_dir_and_prefix(directory: str | Path, prefix="test"):
    return DetectorParams(
        expected_energy_ev=100,
        exposure_time_s=1.0,
        directory=directory,  # type: ignore
        prefix=prefix,
        detector_distance=1.0,
        omega_start=0.0,
        omega_increment=0.0,
        num_images_per_trigger=1,
        num_triggers=1,
        use_roi_mode=False,
        det_dist_to_beam_converter_path=TEST_LUT_TXT,
        detector_size_constants=EIGER2_X_16M_SIZE,
        run_number=123456,
    )


def test_if_string_provided_check_is_dir(tmp_path: Path):
    assert not (_dir := str(tmp_path)).endswith("/")
    params = create_det_params_with_dir_and_prefix(_dir)
    assert params.directory == f"{tmp_path}/"
    file_path = tmp_path / "foo.h5"
    file_path.touch()
    with pytest.raises(ValidationError):
        create_det_params_with_dir_and_prefix(str(file_path))


def test_if_path_provided_check_is_dir(tmp_path: Path):
    params = create_det_params_with_dir_and_prefix(tmp_path)
    assert params.directory == f"{tmp_path}/"
    file_path = tmp_path / "foo.h5"
    file_path.touch()
    with pytest.raises(ValidationError):
        create_det_params_with_dir_and_prefix(file_path)


@patch(
    "dodal.devices.detector.detector.get_config_client",
)
@patch(
    "dodal.devices.detector.det_dist_to_beam_converter.linear_extrapolation_lut",
)
def test_correct_det_dist_to_beam_converter_path_passed_in(
    mock_lut, mock_get_config_client, tmp_path
):
    params = DetectorParams(
        expected_energy_ev=100,
        exposure_time_s=1.0,
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


def test_detector_params_is_serialisable(tmp_path):
    params = DetectorParams(
        expected_energy_ev=100,
        exposure_time_s=1.0,
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
        run_number=123456,
    )
    json = params.model_dump_json()
    new_params = DetectorParams.model_validate_json(json)
    assert new_params == params


# Until https://github.com/DiamondLightSource/dodal/issues/775
def test_detector_params_deserialisation_unchanged(tmp_path: Path):
    # The `directory` parameter in the `create_det_params_with_dir_and_prefix` function is used to
    # specify the directory path where the detector data will be saved. This function creates an
    # instance of `DetectorParams` with the provided directory path and other default parameters. The
    # `directory` parameter can accept either a string or a `Path` object, and it is used to set the
    # `directory` attribute of the `DetectorParams` instance.
    json = f'{{"expected_energy_ev": 100.0, \
    "exposure_time_s": 1.0, \
    "directory": "{tmp_path}", \
    "prefix": "test", \
    "detector_distance": 1.0, \
    "omega_start": 0.0, \
    "omega_increment": 0.0, \
    "num_images_per_trigger": 1, \
    "num_triggers": 1, \
    "use_roi_mode": false, \
    "det_dist_to_beam_converter_path": "a fake directory", \
    "run_number": 17, \
    "trigger_mode": 1, \
    "detector_size_constants": "EIGER2_X_16M", \
    "enable_dev_shm": false}}'
    assert '"run_number": 17' in json
    new_params = DetectorParams.model_validate_json(json)
    assert new_params.run_number == 17
