import numpy as np

from dodal.devices.util.lookup_tables import energy_distance_table
from dodal.log import LOGGER

LUT_COMMENTS = ["#"]
HU_SKIP_ROWS = 3

# Physics constants
ELECTRON_REST_ENERGY_MEV = 0.510999

# Columns in the lookup table
RING_ENERGY_COLUMN = 1
MAGNET_FIELD_COLUMN = 2
MIN_ENERGY_COLUMN = 3
MAX_ENERGY_COLUMN = 4
GAP_OFFSET_COLUMN = 7


async def get_hu_lut_as_dict(lut_path: str) -> dict:
    lut_dict: dict = {}
    _lookup_table: np.ndarray = await energy_distance_table(
        lut_path,
        comments=LUT_COMMENTS,
        skiprows=HU_SKIP_ROWS,
    )
    for i in range(_lookup_table.shape[0]):
        lut_dict[_lookup_table[i][0]] = _lookup_table[i]
        # LOGGER.debug(f"Loaded lookup table:\n {lut_dict}")
    return lut_dict


def calculate_gap_i09_hu(
    photon_energy_kev: float,
    look_up_table: dict[int, "np.ndarray"],
    order: int = 1,
    gap_offset: float = 0.0,
    undulator_period_mm: int = 27,
) -> float:
    """
    Calculate the undulator gap required to produce a given energy at a given harmonic order.
    This algorithm was provided by the I09 beamline scientists, and is based on the physics of undulator radiation.
    https://cxro.lbl.gov//PDF/X-Ray-Data-Booklet.pdf

    Args:
        photon_energy_kev (float): Requested photon energy in keV.
        look_up_table (dict[int, np.ndarray]): Lookup table containing undulator and beamline parameters for each harmonic order.
        order (int, optional): Harmonic order for which to calculate the gap. Defaults to 1.
        gap_offset (float, optional): Additional gap offset to apply (in mm). Defaults to 0.0.
        undulator_period_mm (int, optional): Undulator period in mm. Defaults to 27.

    Returns:
        float: Calculated undulator gap in millimeters.
    """
    magnet_blocks_per_period = 4
    magnet_block_height_mm = 16

    if order not in look_up_table.keys():
        raise ValueError(f"Order parameter {order} not found in lookup table")

    gamma = 1000 * look_up_table[order][RING_ENERGY_COLUMN] / ELECTRON_REST_ENERGY_MEV

    # Constructive interference of radiation emitted at different poles
    # lamda = (lambda_u/2*gamma^2)*(1+K^2/2 + gamma^2*theta^2)/n for n=1,2,3...
    # theta is the observation angle, assumed to be 0 here.
    # Rearranging for K (the undulator parameter, related to magnetic field and gap)
    # gives K^2 = 2*((2*n*gamma^2*lamda/lambda_u)-1)

    undulator_parameter_sqr = (
        4.959368e-6
        * (order * gamma * gamma / (undulator_period_mm * photon_energy_kev))
        - 2
    )
    if undulator_parameter_sqr < 0:
        raise ValueError(
            f"Diffraction parameter squared must be positive! Calculated value {undulator_parameter_sqr}."
        )
    undulator_parameter = np.sqrt(undulator_parameter_sqr)

    # Undulator_parameter K is also defined as K = 0.934*B0[T]*lambda_u[cm],
    # where B0[T] is a peak magnetic field that must depend on gap,
    # but in our LUT it is does not depend on gap, so it's a factor,
    # leading to K = 0.934*B0[T]*lambda_u[cm]*exp(-pi*gap/lambda_u) or
    # K = undulator_parameter_max*exp(-pi*gap/lambda_u)
    # Calculating undulator_parameter_max gives:
    undulator_parameter_max = (
        (
            2
            * 0.0934
            * undulator_period_mm
            * look_up_table[order][MAGNET_FIELD_COLUMN]
            * magnet_blocks_per_period
            / np.pi
        )
        * np.sin(np.pi / magnet_blocks_per_period)
        * (1 - np.exp(-2 * np.pi * magnet_block_height_mm / undulator_period_mm))
    )

    # Finnaly, rearranging the equation:
    # undulator_parameter = undulator_parameter_max*exp(-pi*gap/lambda_u) for gap gives
    gap = (
        (undulator_period_mm / np.pi)
        * np.log(undulator_parameter_max / undulator_parameter)
        + look_up_table[order][GAP_OFFSET_COLUMN]
        + gap_offset
    )
    LOGGER.debug(
        f"Calculated gap is {gap}mm for energy {photon_energy_kev}keV at order {order}"
    )

    return gap
