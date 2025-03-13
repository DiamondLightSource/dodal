from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from numpy import isclose

from dodal.devices.detector import DetectorParams
from dodal.devices.detector.det_resolution import (
    resolution,
)


@pytest.fixture(scope="function")
def detector_params(request, tmp_path: Path):
    return DetectorParams(
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
        use_roi_mode=True,
        det_dist_to_beam_converter_path="tests/test_data/test_det_dist_converter.txt",
        detector_size_constants=request.param,  # type: ignore
    )


@pytest.mark.parametrize(
    "detector_params, roi, wavelength_angstroms, det_distance_mm, expected_res",
    [("EIGER2_X_16M", False, 0.9795, 289.3, 1.5722)],
    indirect=["detector_params"],
)
@patch("dodal.devices.detector.det_resolution._get_detector_max_size_mm")
def test_resolution(
    get_detector_max_size,
    detector_params,
    roi,
    wavelength_angstroms,
    det_distance_mm,
    expected_res,
):
    with mock.patch(
        "dodal.devices.detector.DetectorParams.beam_xy_converter",
        new_callable=PropertyMock,
    ) as prop_patch:
        beam_xy_converter = MagicMock()
        beam_xy_converter.get_beam_xy_from_det_dist.side_effect = [212.51, 219.98]
        prop_patch.return_value = beam_xy_converter
        detector_params.detector_distance = det_distance_mm
        detector_params.use_roi_mode = roi
        get_detector_max_size.return_value = 434.6
        actual_res = resolution(detector_params, wavelength_angstroms, det_distance_mm)
    assert isclose(expected_res, actual_res), (
        f"expected={expected_res}, actual={actual_res}"
    )


@pytest.mark.parametrize(
    "detector_params, roi, wavelength_angstroms, det_distance_mm, expected_res",
    [
        ("EIGER2_X_16M", True, 0.9795, 289.3, 2.26847),
    ],
    indirect=["detector_params"],
)
@patch("dodal.devices.detector.det_resolution._get_detector_max_size_mm")
def test_resolution_with_roi(
    get_detector_max_size,
    detector_params,
    roi,
    wavelength_angstroms,
    det_distance_mm,
    expected_res,
):
    with mock.patch(
        "dodal.devices.detector.DetectorParams.beam_xy_converter",
        new_callable=PropertyMock,
    ) as prop_patch:
        beam_xy_converter = MagicMock()
        beam_xy_converter.get_beam_xy_from_det_dist.side_effect = [212.51, 219.98]
        prop_patch.return_value = beam_xy_converter
        detector_params.detector_distance = det_distance_mm
        detector_params.use_roi_mode = roi
        get_detector_max_size.return_value = 434.6
        actual_res = resolution(detector_params, wavelength_angstroms, det_distance_mm)

    assert isclose(
        actual_res,
        expected_res,
    ), f"expected={expected_res}, actual={actual_res}"


@pytest.mark.parametrize(
    "detector_params, roi, wavelength_angstroms, det_distance_mm, expected_res",
    [
        ("EIGER2_X_16M", True, 0.976238, 289.289, 3.831388),
        ("EIGER2_X_16M", True, 0.976277, 285.82, 3.787823),
        ("EIGER2_X_16M", True, 0.976284, 285.82, 3.787853),
        ("EIGER2_X_16M", True, 0.976246, 370.428, 4.859842),
        ("EIGER2_X_16M", True, 0.976277, 272.9, 3.625220),
        ("EIGER2_X_16M", True, 0.97623, 391.236, 5.124842),
        ("EIGER2_X_16M", True, 0.97623, 196.744, 2.677350),
        ("EIGER2_X_16M", True, 1.28243, 203.756, 3.6282),
        ("EIGER2_X_16M", True, 1.65314, 150, 3.57282),
        ("EIGER2_X_16M", True, 1.65314, 199.96, 4.59785),
        ("EIGER2_X_16M", True, 1.00008, 333.096, 4.4908),
        ("EIGER2_X_16M", True, 0.918415, 312.488, 3.875),
        ("EIGER2_X_16M", True, 0.70541, 201.8, 1.97832),
        ("EIGER2_X_16M", False, 0.705422, 150, 0.909053),
    ],
    indirect=["detector_params"],
)
def test_resolution_with_roi_realistic(
    detector_params,
    roi,
    wavelength_angstroms,
    det_distance_mm,
    expected_res,
):
    detector_params.use_roi_mode = roi
    detector_params.detector_distance = det_distance_mm

    actual_res = resolution(detector_params, wavelength_angstroms, det_distance_mm)

    assert isclose(actual_res, expected_res, rtol=1e-3), (
        f"expected={expected_res}, actual={actual_res}"
    )
