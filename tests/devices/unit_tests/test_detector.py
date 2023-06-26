from unittest.mock import patch

from dodal.devices.detector import DetectorParams


def create_detector_params_with_directory(directory):
    return DetectorParams(
        current_energy_ev=100,
        exposure_time=1.0,
        directory=directory,
        prefix="test",
        run_number=0,
        detector_distance=1.0,
        omega_start=0.0,
        omega_increment=0.0,
        num_images_per_trigger=1,
        num_triggers=1,
        use_roi_mode=False,
        det_dist_to_beam_converter_path="tests/devices/unit_tests/test_lookup_table.txt",
        detector_size_constants="EIGER2_X_16M",
    )


def test_if_trailing_slash_not_provided_then_appended():
    params = create_detector_params_with_directory("test/dir")
    assert params.directory == "test/dir/"


def test_if_trailing_slash_provided_then_not_appended():
    params = create_detector_params_with_directory("test/dir/")
    assert params.directory == "test/dir/"


@patch(
    "src.dodal.devices.detector.DetectorDistanceToBeamXYConverter.parse_table",
)
def test_correct_det_dist_to_beam_converter_path_passed_in(mocked_parse_table):
    params = DetectorParams(
        current_energy_ev=100,
        exposure_time=1.0,
        directory="directory",
        prefix="test",
        run_number=0,
        detector_distance=1.0,
        omega_start=0.0,
        omega_increment=0.0,
        num_images_per_trigger=1,
        num_triggers=1,
        use_roi_mode=False,
        det_dist_to_beam_converter_path="a fake directory",
        detector_size_constants="EIGER2_X_16M",
    )
    params.json()
    assert params.beam_xy_converter.lookup_file == "a fake directory"
