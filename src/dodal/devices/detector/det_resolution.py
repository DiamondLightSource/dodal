from math import atan, sin

from dodal.devices.detector import DetectorParams
from dodal.devices.detector.det_dist_to_beam_converter import (
    Axis,
)


def _get_detector_radius_mm(detector_params: DetectorParams):
    return 0.5 * _get_detector_max_size_mm(detector_params)


def _get_detector_max_size_mm(detector_params):
    return max(
        detector_params.detector_size_constants.det_dimension.width,
        detector_params.detector_size_constants.det_dimension.height,
    )


def _get_beam_xy_accounting_for_roi(detector_params, det_distance_mm):
    beam_x = detector_params.beam_xy_converter.get_beam_xy_from_det_dist(
        det_distance_mm, Axis.X_AXIS
    )
    beam_y = detector_params.beam_xy_converter.get_beam_xy_from_det_dist(
        det_distance_mm, Axis.Y_AXIS
    )
    if detector_params.use_roi_mode:
        size_constants = detector_params.detector_size_constants
        offset_x = 0.5 * (
            size_constants.det_dimension.width - size_constants.roi_dimension.width
        )
        offset_y = 0.5 * (
            size_constants.det_dimension.height - size_constants.roi_dimension.height
        )
        beam_x = beam_x - offset_x
        beam_y = beam_y - offset_y

    return beam_x, beam_y


def _calc_useful_radius(detector_radius_mm, beam_x_mm, beam_y_mm):
    beam_x_from_centre = abs(beam_x_mm - detector_radius_mm)
    beam_y_from_centre = abs(beam_y_mm - detector_radius_mm)
    return detector_radius_mm - max(beam_x_from_centre, beam_y_from_centre)


def _calc_res_at_angle(wavelength_angstroms, angular_shift_radians):
    """Base definition of maximum resolution (from Bragg's Law with n=1)"""
    return 0.5 * wavelength_angstroms / sin(angular_shift_radians)


def _calc_res_off_axis_detector(
    wavelength_angstroms, usable_radius, det_distance_mm, two_theta_radians
):
    """
    Calculate maximum resolution given detector distance and extent (radius) that detector face extends
    No correction for position of beam centre on detector face at twoTheta=0
    Here radius and distance parameters can be in any length unit, provided it is the same, millimetres is the convention
    """
    angular_shift_radians = atan(usable_radius / det_distance_mm)
    return _calc_res_at_angle(
        wavelength_angstroms, 0.5 * (angular_shift_radians + two_theta_radians)
    )


def _max_res_for_mx(
    wavelength_angstroms, detector_radius_mm, det_distance_mm, beam_x_mm, beam_y_mm
):
    """
    Calculate maximum resolution given MX Use Case (detector at twoTheta=0) and beam centre on detector face
    Correct the radius for position of beam centre on detector face at twoTheta=0
    """
    usable_radius = _calc_useful_radius(detector_radius_mm, beam_x_mm, beam_y_mm)
    return _calc_res_off_axis_detector(
        wavelength_angstroms, usable_radius, det_distance_mm, 0
    )


def resolution(
    detector_params: DetectorParams, wavelength_angstroms: float, det_distance_mm: float
):
    detector_radius_mm = _get_detector_radius_mm(detector_params)
    (beam_x_mm, beam_y_mm) = _get_beam_xy_accounting_for_roi(
        detector_params, det_distance_mm
    )

    return _max_res_for_mx(
        wavelength_angstroms, detector_radius_mm, det_distance_mm, beam_x_mm, beam_y_mm
    )
