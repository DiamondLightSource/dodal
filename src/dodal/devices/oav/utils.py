import numpy as np


def bottom_right_from_top_left(
    top_left: np.ndarray,
    steps_x: int,
    steps_y: int,
    step_size_x: float,
    step_size_y: float,
    pix_per_um_x: float,
    pix_per_um_y: float,
) -> np.ndarray:
    return np.array(
        [
            # step size is given in mm, pix in um
            int(steps_x * step_size_x * 1000 * pix_per_um_x + top_left[0]),
            int(steps_y * step_size_y * 1000 * pix_per_um_y + top_left[1]),
        ],
        dtype=np.dtype(int),
    )
