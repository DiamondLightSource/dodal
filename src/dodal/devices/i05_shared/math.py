"""
Helper functions that can perform rotations on x and y. A matrix of callables is used so
that any rotation can be used.

from numpy import cos as c
from numpy import sin as s

def neg_s(x: float) -> float:
    return -s(x)

ROTATION_MATRIX = [[c, s], [neg_s, c]]
x, y = 1, 5

new_x, new_y = rotate_deg(45, x, y, ROTATION_MATRIX)
"""

from collections.abc import Callable

import numpy as np

CallableRotationMatrixType = tuple[
    tuple[Callable[[float], float], Callable[[float], float]],
    tuple[Callable[[float], float], Callable[[float], float]],
]


def _get_rotation_matrix(
    theta: float, callable_rotation_matrix: CallableRotationMatrixType
) -> np.ndarray:
    return np.array(
        [
            [fn(theta) for fn in row_functions]
            for row_functions in callable_rotation_matrix
        ]
    )


def rotate(
    theta: float,
    x: float,
    y: float,
    callable_rotation_matrix: CallableRotationMatrixType,
    inverse: bool = False,
) -> tuple[float, float]:
    rotation_matrix = _get_rotation_matrix(theta, callable_rotation_matrix)
    if inverse:
        rotation_matrix = rotation_matrix.T
    positions = np.array([x, y])
    rotation = rotation_matrix @ positions
    return rotation[0], rotation[1]
