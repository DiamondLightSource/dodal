import numpy as np

"""
| Rotation | Formula for X_rot | Formula for Y_rot |
| -------- | ----------------- | ----------------- |
| CW       | x cosθ + y sinθ   | -x sinθ + y cosθ  |
| CCW      | x cosθ - y sinθ   | x sinθ + y cosθ   |
"""


def do_rotation(x: float, y: float, rotation_matrix: np.ndarray) -> tuple[float, float]:
    positions = np.array([x, y])
    rotation = rotation_matrix @ positions
    return float(rotation[0]), float(rotation[1])


def rotate_clockwise(
    theta: float,
    x: float,
    y: float,
) -> tuple[float, float]:
    rotation_matrix = np.array(
        [
            [np.cos(theta), np.sin(theta)],
            [-np.sin(theta), np.cos(theta)],
        ]
    )
    return do_rotation(x, y, rotation_matrix)


def rotate_counter_clockwise(
    theta: float,
    x: float,
    y: float,
) -> tuple[float, float]:
    rotation_matrix = np.array(
        [
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)],
        ]
    )
    return do_rotation(x, y, rotation_matrix)
