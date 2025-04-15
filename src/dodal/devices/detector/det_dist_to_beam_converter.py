from enum import Enum

from dodal.devices.util.lookup_tables import (
    linear_extrapolation_lut,
    parse_lookup_table,
)


class Axis(Enum):
    X_AXIS = 1
    Y_AXIS = 2


class DetectorDistanceToBeamXYConverter:
    def __init__(self, lookup_file: str):
        self.lookup_file: str = lookup_file
        lookup_table_columns: list = parse_lookup_table(self.lookup_file)
        self._d_to_x = linear_extrapolation_lut(
            lookup_table_columns[0], lookup_table_columns[1]
        )
        self._d_to_y = linear_extrapolation_lut(
            lookup_table_columns[0], lookup_table_columns[2]
        )

    def get_beam_xy_from_det_dist(self, det_dist_mm: float, beam_axis: Axis) -> float:
        return (
            self._d_to_x(det_dist_mm)
            if beam_axis == Axis.X_AXIS
            else self._d_to_y(det_dist_mm)
        )

    def get_beam_axis_pixels(
        self,
        det_distance: float,
        image_size_pixels: int,
        det_dim: float,
        beam_axis: Axis,
    ) -> float:
        beam_mm = self.get_beam_xy_from_det_dist(det_distance, beam_axis)
        return beam_mm * image_size_pixels / det_dim

    def get_beam_y_pixels(
        self, det_distance: float, image_size_pixels: int, det_dim: float
    ) -> float:
        return self.get_beam_axis_pixels(
            det_distance, image_size_pixels, det_dim, Axis.Y_AXIS
        )

    def get_beam_x_pixels(
        self, det_distance: float, image_size_pixels: int, det_dim: float
    ) -> float:
        return self.get_beam_axis_pixels(
            det_distance, image_size_pixels, det_dim, Axis.X_AXIS
        )
