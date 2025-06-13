from math import isclose
from unittest.mock import Mock, patch

import pytest

from dodal.devices.detector.det_dist_to_beam_converter import (
    Axis,
    DetectorDistanceToBeamXYConverter,
)

# fmt: off
LOOKUP_TABLE_TEST_VALUES = [
    (100.0, 200.0),  # distance
    (150.0, 151.0),  # x
    (160.0, 165.0),  # y
]
# fmt: on


@pytest.fixture
def fake_converter():
    with patch(
        "dodal.devices.detector.det_dist_to_beam_converter.parse_lookup_table",
        return_value=LOOKUP_TABLE_TEST_VALUES,
    ):
        yield DetectorDistanceToBeamXYConverter("test.txt")


@pytest.mark.parametrize(
    "detector_distance, axis, expected_value",
    [
        (100.0, Axis.Y_AXIS, 160.0),
        (200.0, Axis.X_AXIS, 151.0),
        (150.0, Axis.X_AXIS, 150.5),
        (190.0, Axis.Y_AXIS, 164.5),
    ],
)
def test_interpolate_beam_xy_from_det_distance(
    fake_converter: DetectorDistanceToBeamXYConverter,
    detector_distance: float,
    axis: Axis,
    expected_value: float,
):
    assert isinstance(
        fake_converter.get_beam_xy_from_det_dist(detector_distance, axis), float
    )

    assert (
        fake_converter.get_beam_xy_from_det_dist(detector_distance, axis)
        == expected_value
    )


@pytest.mark.parametrize(
    "detector_distance, axis, expected_value",
    [
        (95.0, Axis.X_AXIS, 149.95),
        (205.0, Axis.X_AXIS, 151.05),
        (95.0, Axis.Y_AXIS, 159.75),
        (205.0, Axis.Y_AXIS, 165.25),
    ],
)
def test_extrapolate_beam_xy_from_det_distance(
    fake_converter: DetectorDistanceToBeamXYConverter,
    detector_distance: float,
    axis: Axis,
    expected_value: float,
):
    actual = fake_converter.get_beam_xy_from_det_dist(detector_distance, axis)
    assert isclose(actual, expected_value), f"was {actual} expected {expected_value}"


def test_get_beam_in_pixels(fake_converter: DetectorDistanceToBeamXYConverter):
    detector_distance = 100.0
    image_size_pixels = 100
    detector_dimensions = 200.0
    interpolated_x_value = 150.0
    interpolated_y_value = 160.0

    def mock_callback(dist: float, axis: Axis):
        match axis:
            case Axis.X_AXIS:
                return interpolated_x_value
            case Axis.Y_AXIS:
                return interpolated_y_value

    fake_converter.get_beam_xy_from_det_dist = Mock()
    fake_converter.get_beam_xy_from_det_dist.side_effect = mock_callback
    expected_y_value = interpolated_y_value * image_size_pixels / detector_dimensions
    expected_x_value = interpolated_x_value * image_size_pixels / detector_dimensions

    calculated_y_value = fake_converter.get_beam_y_pixels(
        detector_distance, image_size_pixels, detector_dimensions
    )

    assert calculated_y_value == expected_y_value
    assert (
        fake_converter.get_beam_x_pixels(
            detector_distance, image_size_pixels, detector_dimensions
        )
        == expected_x_value
    )
