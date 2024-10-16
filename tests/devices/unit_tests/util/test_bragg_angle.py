import math

import pytest

from dodal.devices.util.bragg_angle import energy_to_bragg_angle


@pytest.mark.parametrize("input_energy_kev, expected_bragg_angle_deg",
                         [
                             [7, 16.41],
                             [8, 14.31],
                             [11, 10.35],
                             [12.3, 9.25],
                             [15, 7.57]
                          ])
def test_energy_to_bragg_angle(input_energy_kev: float,
                               expected_bragg_angle_deg: float):
    assert math.isclose(energy_to_bragg_angle(input_energy_kev),
                        expected_bragg_angle_deg,
                        abs_tol=0.01)
