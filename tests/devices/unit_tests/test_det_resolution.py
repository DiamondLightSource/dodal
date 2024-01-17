from unittest.mock import MagicMock, patch

import pytest
from numpy import isclose

from dodal.devices.det_resolution import resolution
from dodal.devices.detector import DetectorParams


@pytest.fixture()
def detector_params():
    return DetectorParams(
        expected_energy_ev=100,
        exposure_time=1.0,
        directory="test/dir",
        prefix="test",
        run_number=0,
        detector_distance=1.0,
        omega_start=0.0,
        omega_increment=0.0,
        num_images_per_trigger=1,
        num_triggers=1,
        use_roi_mode=False,
        det_dist_to_beam_converter_path="tests/devices/unit_tests/test_lookup_table.txt",
        detector_size_constants="EIGER2_X_16M",  # type: ignore
    )


@pytest.mark.parametrize(
    "roi, wavelength_angstroms, det_distance_mm, expected_res",
    [(False, 0.9795, 289.3, 1.5722)],
)
@patch("dodal.devices.det_resolution._get_detector_max_size_mm")
def test_resolution(
    get_detector_max_size,
    detector_params,
    roi,
    wavelength_angstroms,
    det_distance_mm,
    expected_res,
):
    detector_params.detector_distance = det_distance_mm
    detector_params.beam_xy_converter.get_beam_xy_from_det_dist = MagicMock(
        side_effect=[212.51, 219.98]
    )
    get_detector_max_size.return_value = 434.6
    actual_res = resolution(detector_params, wavelength_angstroms, det_distance_mm)
    assert isclose(
        expected_res, actual_res
    ), f"expected={expected_res}, actual={actual_res}"


@pytest.mark.parametrize(
    "roi, wavelength_angstroms, det_distance_mm, expected_res",
    [(True, 0.9795, 289.3, 2.26847)],
)
@patch("dodal.devices.det_resolution._get_detector_max_size_mm")
def test_resolution_with_roi(
    get_detector_max_size,
    detector_params,
    roi,
    wavelength_angstroms,
    det_distance_mm,
    expected_res,
):
    detector_params.use_roi_mode = roi
    detector_params.detector_distance = det_distance_mm
    detector_params.beam_xy_converter.get_beam_xy_from_det_dist = MagicMock(
        side_effect=[212.51, 219.98]
    )
    get_detector_max_size.return_value = 434.6

    actual_res = resolution(detector_params, wavelength_angstroms, det_distance_mm)

    assert isclose(
        expected_res, actual_res
    ), f"expected={expected_res}, actual={actual_res}"
