from unittest.mock import MagicMock, patch

from dodal.devices.detector import DetectorParams


def create_det_params_with_dir_and_prefix(directory, prefix="test"):
    return DetectorParams(
        expected_energy_ev=100,
        exposure_time=1.0,
        directory=directory,
        prefix=prefix,
        detector_distance=1.0,
        omega_start=0.0,
        omega_increment=0.0,
        num_images_per_trigger=1,
        num_triggers=1,
        use_roi_mode=False,
        det_dist_to_beam_converter_path="tests/devices/unit_tests/test_lookup_table.txt",
        detector_size_constants="EIGER2_X_16M",
    )  # type: ignore


def test_if_trailing_slash_not_provided_then_appended(tmp_path):
    assert not (_dir := str(tmp_path)).endswith("/")
    params = create_det_params_with_dir_and_prefix(_dir)
    assert params.directory == _dir + "/"


def test_if_trailing_slash_provided_then_not_appended(tmp_path):
    assert not (_dir := str(tmp_path)).endswith("/")
    params = create_det_params_with_dir_and_prefix(_dir + "/")
    assert params.directory == _dir + "/"
    assert not params.directory.endswith("//")


@patch(
    "src.dodal.devices.detector.DetectorDistanceToBeamXYConverter.parse_table",
)
def test_correct_det_dist_to_beam_converter_path_passed_in(mocked_parse_table):
    params = DetectorParams(
        expected_energy_ev=100,
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


@patch(
    "src.dodal.devices.detector.DetectorDistanceToBeamXYConverter.parse_table",
)
def test_run_number_correct_when_not_specified(mocked_parse_table, tmpdir):
    params = DetectorParams(
        expected_energy_ev=100,
        exposure_time=1.0,
        directory=str(tmpdir),
        prefix="test",
        detector_distance=1.0,
        omega_start=0.0,
        omega_increment=0.0,
        num_images_per_trigger=1,
        num_triggers=1,
        use_roi_mode=False,
        det_dist_to_beam_converter_path="a fake directory",
        detector_size_constants="EIGER2_X_16M",
    )
    assert params.run_number == 1


@patch(
    "src.dodal.devices.detector.DetectorDistanceToBeamXYConverter.parse_table",
)
def test_run_number_correct_when_specified(mocked_parse_table, tmpdir):
    params = DetectorParams(
        expected_energy_ev=100,
        exposure_time=1.0,
        directory=str(tmpdir),
        run_number=6,
        prefix="test",
        detector_distance=1.0,
        omega_start=0.0,
        omega_increment=0.0,
        num_images_per_trigger=1,
        num_triggers=1,
        use_roi_mode=False,
        det_dist_to_beam_converter_path="a fake directory",
        detector_size_constants="EIGER2_X_16M",
    )
    assert params.run_number == 6


@patch("os.listdir")
def test_prefix_is_used_to_determine_run_number(mock_listdir: MagicMock):
    foos = (f"foo_{i}.nxs" for i in range(4))
    bars = (f"bar_{i}.nxs" for i in range(7))
    bazs = (f"baz_{i}.nxs" for i in range(23, 29))
    files = [*foos, *bars, *bazs]
    mock_listdir.return_value = files

    assert create_det_params_with_dir_and_prefix("dir", "foo").run_number == 4
    assert create_det_params_with_dir_and_prefix("dir", "bar").run_number == 7
    assert create_det_params_with_dir_and_prefix("dir", "baz").run_number == 29
    assert create_det_params_with_dir_and_prefix("dir", "qux").run_number == 1
