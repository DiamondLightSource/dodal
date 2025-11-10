from unittest.mock import patch

import numpy as np
import pytest

from dodal.devices.oav.pin_image_recognition.utils import (
    NONE_VALUE,
    MxSampleDetect,
    ScanDirections,
    blur,
    close,
    gaussian_blur,
    identity,
    median_blur,
    open_morph,
)


@pytest.fixture
def sample_array():
    return np.array(
        [
            [0, 0, 0, 0, 0],
            [0, 120, 120, 120, 0],
            [0, 120, 127, 120, 0],
            [0, 120, 120, 120, 0],
            [0, 0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )


def test_locate_sample_simple_forward():
    test_arr = np.array(
        [
            [0, 0, 0, 0, 0],
            [0, 1, 1, 1, 0],
            [0, 1, 0, 1, 1],
            [0, 1, 1, 1, 0],
            [0, 0, 0, 0, 0],
        ],
        dtype=np.int32,
    )

    location = MxSampleDetect(min_tip_height=1)._locate_sample(test_arr)

    assert location.edge_top is not None
    assert location.edge_bottom is not None

    np.testing.assert_array_equal(
        location.edge_top, np.array([NONE_VALUE, 1, 1, 1, 2], dtype=np.int32)
    )
    np.testing.assert_array_equal(
        location.edge_bottom, np.array([NONE_VALUE, 3, 3, 3, 2], dtype=np.int32)
    )

    assert location.tip_x == 1
    assert location.tip_y == 2


def test_locate_sample_simple_reverse():
    test_arr = np.array(
        [
            [0, 0, 0, 0, 0],
            [0, 1, 1, 1, 0],
            [1, 1, 0, 1, 0],
            [0, 1, 1, 1, 0],
            [0, 0, 0, 0, 0],
        ],
        dtype=np.int32,
    )

    location = MxSampleDetect(
        min_tip_height=1, scan_direction=ScanDirections.REVERSE
    )._locate_sample(test_arr)

    assert location.edge_top is not None
    assert location.edge_bottom is not None

    np.testing.assert_array_equal(
        location.edge_top, np.array([2, 1, 1, 1, NONE_VALUE], dtype=np.int32)
    )
    np.testing.assert_array_equal(
        location.edge_bottom, np.array([2, 3, 3, 3, NONE_VALUE], dtype=np.int32)
    )

    assert location.tip_x == 3
    assert location.tip_y == 2


def test_locate_sample_no_edges():
    test_arr = np.array(
        [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        dtype=np.int32,
    )

    location = MxSampleDetect(min_tip_height=1)._locate_sample(test_arr)

    assert location.edge_top is not None
    assert location.edge_bottom is not None

    np.testing.assert_array_equal(
        location.edge_top,
        np.broadcast_to(np.array([NONE_VALUE], dtype=np.int32), (5,)),
    )
    np.testing.assert_array_equal(
        location.edge_bottom,
        np.broadcast_to(np.array([NONE_VALUE], dtype=np.int32), (5,)),
    )

    assert location.tip_x is None
    assert location.tip_y is None


@pytest.mark.parametrize(
    "direction,x_centre", [(ScanDirections.FORWARD, 0), (ScanDirections.REVERSE, 4)]
)
def test_locate_sample_tip_off_screen(direction, x_centre):
    test_arr = np.array(
        [
            [0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0],
        ],
        dtype=np.int32,
    )

    location = MxSampleDetect(
        min_tip_height=1, scan_direction=direction
    )._locate_sample(test_arr)

    assert location.edge_top is not None
    assert location.edge_bottom is not None

    np.testing.assert_array_equal(
        location.edge_top, np.array([1, 1, 1, 1, 1], dtype=np.int32)
    )
    np.testing.assert_array_equal(
        location.edge_bottom, np.array([3, 3, 3, 3, 3], dtype=np.int32)
    )

    # Currently sample "off screen" is not considered an error so a centre is still returned.
    assert location.tip_x == x_centre
    assert location.tip_y == 2


@pytest.mark.parametrize(
    "min_tip_width,sample_x_location,expected_top_edge,expected_bottom_edge",
    [
        (1, 0, [2, NONE_VALUE, 1, 0, 0], [2, NONE_VALUE, 3, 4, 4]),
        (3, 2, [NONE_VALUE, NONE_VALUE, 1, 0, 0], [NONE_VALUE, NONE_VALUE, 3, 4, 4]),
    ],
)
def test_locate_sample_with_min_tip_height(
    min_tip_width, sample_x_location, expected_top_edge, expected_bottom_edge
):
    # "noise" at (0, 2) should be ignored by "min tip width" mechanism if it has min width >1
    # Tip should therefore be detected at (2, 2) for min_tip_width = 3, or (0, 2) for min_tip_width = 1
    test_arr = np.array(
        [
            [0, 0, 0, 1, 1],
            [0, 0, 1, 0, 0],
            [1, 0, 1, 0, 0],
            [0, 0, 1, 0, 0],
            [0, 0, 0, 1, 1],
        ],
        dtype=np.int32,
    )

    location = MxSampleDetect(min_tip_height=min_tip_width)._locate_sample(test_arr)

    assert location.edge_top is not None
    assert location.edge_bottom is not None

    # Even though an edge is detected at x=4, it should be explicitly set to NONE_VALUE
    # as this is past the detected "tip"
    np.testing.assert_array_equal(
        location.edge_top, np.array(expected_top_edge, dtype=np.int32)
    )
    np.testing.assert_array_equal(
        location.edge_bottom,
        np.array(expected_bottom_edge, dtype=np.int32),
    )

    assert location.tip_x == sample_x_location
    assert location.tip_y == 2


def test_first_and_last_nonzero_by_columns():
    test_arr = np.array(
        [
            [0, 0, 0, 1],
            [1, 1, 0, 0],
            [0, 1, 0, 1],
        ],
        dtype=np.int32,
    )

    first, last = MxSampleDetect._first_and_last_nonzero_by_columns(test_arr)

    np.testing.assert_array_equal(first, np.array([1, 1, NONE_VALUE, 0]))
    np.testing.assert_array_equal(last, np.array([1, 2, NONE_VALUE, 2]))


def test_open_close(sample_array):
    open_fn = open_morph(3, 1)
    close_fn = close(3, 1)

    noisy = sample_array.copy()
    noisy[0, 0] = 127
    noisy_with_hole = sample_array.copy()
    noisy_with_hole[2, 2] = 0

    cleaned = open_fn(noisy)
    filled = close_fn(noisy_with_hole)

    assert cleaned[0, 0] == 0
    assert filled[2, 2] >= 120


def test_blur_variants(sample_array):
    blur_fn = blur(3)
    gblur_fn = gaussian_blur(3)
    mblur_fn = median_blur(3)

    blurred = blur_fn(sample_array)
    gblurred = gblur_fn(sample_array)
    mblurred = mblur_fn(sample_array)

    assert blurred[2, 2] < 127
    assert gblurred[2, 2] < 127
    assert mblurred[2, 2] < 127


def test_process_array():
    test_arr = np.array(
        [
            [0, 0, 0, 0, 0],
            [0, 0, 255, 0, 0],
            [0, 0, 255, 0, 0],
            [0, 0, 255, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )

    detector = MxSampleDetect(
        preprocess=identity(),
        open_ksize=0,
        open_iterations=1,
        close_ksize=1,
        close_iterations=1,
        canny_upper=100,
        canny_lower=50,
        min_tip_height=3,
    )

    location = detector.process_array(test_arr)

    assert location.tip_x is not None
    assert location.tip_y is not None

    assert 1 <= location.tip_x <= 3
    assert 1 <= location.tip_y <= 3

    assert isinstance(location.edge_top, np.ndarray)
    assert isinstance(location.edge_bottom, np.ndarray)
    assert location.edge_top.shape == location.edge_bottom.shape


def test_process_array_if_open_ksize_is_not_zero():
    test_arr = np.array(
        [
            [0, 0, 0, 0, 0],
            [0, 0, 255, 0, 0],
            [0, 0, 255, 0, 0],
            [0, 0, 255, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        dtype=np.uint8,
    )

    detector = MxSampleDetect(
        preprocess=identity(),
        open_ksize=1,
        open_iterations=1,
        close_ksize=1,
        close_iterations=1,
        canny_upper=100,
        canny_lower=50,
        min_tip_height=3,
    )

    with patch(
        "dodal.devices.oav.pin_image_recognition.utils.open_morph",
        return_value=lambda arr: arr,
    ) as mock_open_morph:
        location = detector.process_array(test_arr)

        mock_open_morph.assert_called_once()

        assert location.tip_x is not None
        assert location.tip_y is not None

        assert 1 <= location.tip_x <= 3
        assert 1 <= location.tip_y <= 3

        assert isinstance(location.edge_top, np.ndarray)
        assert isinstance(location.edge_bottom, np.ndarray)
        assert location.edge_top.shape == location.edge_bottom.shape
