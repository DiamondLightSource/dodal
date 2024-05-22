from unittest.mock import patch

from dodal.testing_utils import create_new_detector_params


def test_if_trailing_slash_not_provided_then_appended():
    params = create_new_detector_params(directory="test/dir")
    assert params.directory == "test/dir/"


def test_if_trailing_slash_provided_then_not_appended():
    params = create_new_detector_params(directory="test/dir/")
    assert params.directory == "test/dir/"


@patch(
    "src.dodal.devices.detector.DetectorDistanceToBeamXYConverter.parse_table",
)
def test_correct_det_dist_to_beam_converter_path_passed_in(mocked_parse_table):
    params = create_new_detector_params(det_dist_path="a fake directory")
    params.json()
    assert params.beam_xy_converter.lookup_file == "a fake directory"


@patch(
    "src.dodal.devices.detector.DetectorDistanceToBeamXYConverter.parse_table",
)
def test_run_number_correct_when_not_specified(mocked_parse_table, tmpdir):
    params = create_new_detector_params(
        directory=str(tmpdir), det_dist_path="a fake directory", run_number=None
    )

    assert params.run_number == 1


@patch(
    "src.dodal.devices.detector.DetectorDistanceToBeamXYConverter.parse_table",
)
def test_run_number_correct_when_specified(mocked_parse_table, tmpdir):
    params = create_new_detector_params(
        directory=str(tmpdir), det_dist_path="a fake directory", run_number=6
    )
    assert params.run_number == 6
