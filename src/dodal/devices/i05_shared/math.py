from collections.abc import Callable
from dataclasses import dataclass
from math import radians

import numpy as np


@dataclass
class Vector2D:
    """
    Helper class that can perform rotations on x and y. It is configured with a matrix
    of callables so this can be used for any kind of rotation.

    from numpy import cos as c
    from numpy import sin as s

    def neg_s(x: float) -> float:
        return -s(x)

    ROTATION_MATRIX = [[c, s], [neg_s, c]]
    x, y = 1, 5

    vec = Vector2D(x, y, ROTATION_MATRIX)
    new_vec = vec.rotate_deg(45)
    new_x = new_vec.x
    new_y = new_vec.y
    """

    x: float
    y: float
    callable_rotation_matrix: list[list[Callable[[float], float]]]

    def to_array(self) -> np.ndarray:
        return np.array([self.x, self.y])

    @classmethod
    def from_array(
        cls,
        arr: np.ndarray,
        callable_rotation_matrix: list[list[Callable[[float], float]]],
    ) -> "Vector2D":
        return cls(
            x=arr[0], y=arr[1], callable_rotation_matrix=callable_rotation_matrix
        )

    def _rotation_matrix(self, theta) -> np.ndarray:
        return np.array(
            [
                [fn(theta) for fn in row_functions]
                for row_functions in self.callable_rotation_matrix
            ]
        )

    def _inverse_rotation_matrix(self, theta) -> np.ndarray:
        return self._rotation_matrix(theta).T

    def rotate_deg(self, angle_deg: float) -> "Vector2D":
        return self.rotate(radians(angle_deg))

    def rotate(self, theta: float) -> "Vector2D":
        rotated = self._rotation_matrix(theta) @ self.to_array()
        return Vector2D.from_array(rotated, self.callable_rotation_matrix)

    def inverse_rotate_deg(self, angle_deg: float) -> "Vector2D":
        return self.inverse_rotate(radians(angle_deg))

    def inverse_rotate(self, theta: float) -> "Vector2D":
        rotated = self._inverse_rotation_matrix(theta) @ self.to_array()
        return Vector2D.from_array(rotated, self.callable_rotation_matrix)

    def __repr__(self):
        return f"Vector2D(x={self.x}, y={self.y})"
