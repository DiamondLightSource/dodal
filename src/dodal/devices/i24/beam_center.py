"""A small temporary device to get the beam center positions from \
    eiger or pilatus detector on i24"""

from ophyd_async.core import StandardReadable
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.util.lookup_tables import (
    linear_interpolation_lut,
    parse_lookup_table,
)


class DetectorBeamCenter(StandardReadable):
    def __init__(self, prefix: str, lut_path: str, name: str = "") -> None:
        self.beam_x = epics_signal_rw(float, prefix + "BeamX")  # in pixels
        self.beam_y = epics_signal_rw(float, prefix + "BeamY")
        self.lookup = lut_path
        super().__init__(name)

    def compute_beam_center_position_mm(self, det_dist: float) -> tuple[float, float]:
        lut_values = parse_lookup_table(self.lookup)

        calc_x = linear_interpolation_lut(lut_values[0], lut_values[1])
        beam_x = calc_x(det_dist)

        calc_y = linear_interpolation_lut(lut_values[0], lut_values[2])
        beam_y = calc_y(det_dist)

        return beam_x, beam_y
