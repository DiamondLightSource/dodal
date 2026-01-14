import numpy.polynomial as poly

from dodal.common.maths import Rectangle2D
from dodal.devices.insertion_device.enum import Pol

# Define exclusion zones in phase-gap space - not supposed to be crossed during moves
I05_APPLE_KNOT_EXCLUSION_ZONES = (
    Rectangle2D(-65.5, 0.0, 65.5, 25.5),  # mechanical limit
    Rectangle2D(-10.5, 0.0, 10.5, 37.5),  # power load limit
)

I05_LH_GAP_POLYNOMIAL = poly.Polynomial(
    [
        12.464,
        1.8417,
        -0.030139,
        0.00023511,
        1.0158e-6,
        -3.9229e-8,
        3.6772e-10,
        -1.7356e-12,
        4.2103e-15,
        -4.1724e-18,
    ]
)

I05_LV_GAP_POLYNOMIAL = poly.Polynomial(
    [
        8.7456,
        1.1344,
        -0.024317,
        0.00041143,
        -5.0759e-6,
        4.496e-8,
        -2.7464e-10,
        1.081e-12,
        -2.4377e-15,
        2.3749e-18,
    ]
)

I05_C_GAP_POLYNOMIAL = poly.Polynomial(
    [
        9.1763,
        1.4886,
        -0.035968,
        0.00064576,
        -7.951e-6,
        6.6281e-8,
        -3.6547e-10,
        1.2699e-12,
        -2.5078e-15,
        2.1392e-18,
    ]
)

I05_C_PHASE_POLYNOMIAL = poly.Polynomial(
    [
        4.431,
        0.79535,
        -0.022218,
        0.00040781,
        -4.921e-6,
        3.9683e-8,
        -2.1267e-10,
        7.2752e-13,
        -1.4341e-15,
        1.2345e-18,
    ]
)


def energy_to_gap_converter(energy: float, pol: Pol) -> float:
    if pol == Pol.LH:
        return float(I05_LH_GAP_POLYNOMIAL(energy))
    if pol == Pol.LV:
        return float(I05_LV_GAP_POLYNOMIAL(energy))
    if pol == Pol.PC:
        return float(I05_C_GAP_POLYNOMIAL(energy))
    if pol == Pol.NC:
        return -1.0 * float(I05_C_GAP_POLYNOMIAL(energy))
    return 0.0


def gap_to_phase_converter(energy: float, pol: Pol) -> float:
    if pol == Pol.LH:
        return 0.0
    if pol == Pol.LV:
        return 70.0
    if pol == Pol.PC or pol == Pol.NC:
        return float(I05_C_PHASE_POLYNOMIAL(energy))
    return 0.0
