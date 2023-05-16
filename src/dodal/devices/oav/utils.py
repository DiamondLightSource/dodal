from enum import IntEnum

from dodal.utils import Point2D


def bottom_right_from_top_left(
    top_left: Point2D,
    steps_x: int,
    steps_y: int,
    step_size_x: float,
    step_size_y: float,
    pix_per_um_x: float,
    pix_per_um_y: float,
) -> Point2D:
    return Point2D(
        # step size is given in mm, pix in um
        int(steps_x * step_size_x * 1000 * pix_per_um_x + top_left.x),
        int(steps_y * step_size_y * 1000 * pix_per_um_y + top_left.y),
    )


class ColorMode(IntEnum):
    """
    Enum to store the various color modes of the camera. We use RGB1.
    """

    MONO = 0
    BAYER = 1
    RGB1 = 2
    RGB2 = 3
    RGB3 = 4
    YUV444 = 5
    YUV422 = 6
    YUV421 = 7


class EdgeOutputArrayImageType(IntEnum):
    """
    Enum to store the types of image to tweak the output array. We use Original.
    """

    ORIGINAL = 0
    GREYSCALE = 1
    PREPROCESSED = 2
    CANNY_EDGES = 3
    CLOSED_EDGES = 4
