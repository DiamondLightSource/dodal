import numpy as np
import pytest

from dodal.devices.oav.pin_image_recognition.utils import NONE_VALUE, MxSampleDetect


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

    location = MxSampleDetect(min_tip_height=1, scan_direction=-1)._locate_sample(
        test_arr
    )

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


@pytest.mark.parametrize("direction,x_centre", [(1, 0), (-1, 4)])
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

    location = MxSampleDetect(
        min_tip_height=min_tip_width, scan_direction=1
    )._locate_sample(test_arr)

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
