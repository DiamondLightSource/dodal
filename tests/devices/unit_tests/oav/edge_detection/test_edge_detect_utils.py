from dodal.devices.oav.edge_detection.edge_detect_utils import MxSampleDetect

import numpy as np
import pytest


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

    np.testing.assert_array_equal(location.edge_top, np.array([0, 1, 1, 1, 2], dtype=np.int32))
    np.testing.assert_array_equal(location.edge_bottom, np.array([0, 3, 3, 3, 2], dtype=np.int32))

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

    location = MxSampleDetect(min_tip_height=1, scan_direction=-1)._locate_sample(test_arr)

    assert location.edge_top is not None
    assert location.edge_bottom is not None

    np.testing.assert_array_equal(location.edge_top, np.array([2, 1, 1, 1, 0], dtype=np.int32))
    np.testing.assert_array_equal(location.edge_bottom, np.array([2, 3, 3, 3, 0], dtype=np.int32))

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

    np.testing.assert_array_equal(location.edge_top, np.array([0, 0, 0, 0, 0], dtype=np.int32))
    np.testing.assert_array_equal(location.edge_bottom, np.array([0, 0, 0, 0, 0], dtype=np.int32))

    assert location.tip_x == -1
    assert location.tip_y == -1


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

    location = MxSampleDetect(min_tip_height=1, scan_direction=direction)._locate_sample(test_arr)

    assert location.edge_top is not None
    assert location.edge_bottom is not None

    np.testing.assert_array_equal(location.edge_top, np.array([1, 1, 1, 1, 1], dtype=np.int32))
    np.testing.assert_array_equal(location.edge_bottom, np.array([3, 3, 3, 3, 3], dtype=np.int32))

    # Currently sample "off screen" is not considered an error so a centre is still returned.
    # Maybe it should be?
    assert location.tip_x == x_centre
    assert location.tip_y == 2
