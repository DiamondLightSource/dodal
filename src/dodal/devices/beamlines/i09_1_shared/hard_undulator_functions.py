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
MIN_GAP_COLUMN = 5
MAX_GAP_COLUMN = 6
GAP_OFFSET_COLUMN = 7

MAGNET_BLOCKS_PER_PERIOD = 4
MAGNTE_BLOCK_HEIGHT_MM = 16


async def get_hu_lut_as_dict(lut_path: str) -> dict[int, np.ndarray]:
    lut_dict: dict[int, np.ndarray] = {}
    _lookup_table: np.ndarray = await energy_distance_table(
        lut_path,
        comments=LUT_COMMENTS,
        skiprows=HU_SKIP_ROWS,
    )
    for i in range(_lookup_table.shape[0]):
        lut_dict[_lookup_table[i][0]] = _lookup_table[i]
    LOGGER.debug(f"Loaded lookup table: {lut_dict}")
    return lut_dict


def _validate_order(order: int, look_up_table: dict[int, "np.ndarray"]) -> None:
    """Validate that the harmonic order exists in the lookup table."""
    if order not in look_up_table.keys():
        raise ValueError(f"Order parameter {order} not found in lookup table")


def _calculate_gamma(look_up_table: dict[int, "np.ndarray"], order: int) -> float:
    """Calculate the Lorentz factor gamma from the lookup table."""
    return 1000 * look_up_table[order][RING_ENERGY_COLUMN] / ELECTRON_REST_ENERGY_MEV


def _calculate_undulator_parameter_max(
    magnet_field: float, undulator_period_mm: int
) -> float:
    """
    Calculate the maximum undulator parameter.
    """
    return (
        (
            2
            * 0.0934
            * undulator_period_mm
            * magnet_field
            * MAGNET_BLOCKS_PER_PERIOD
            / np.pi
        )
        * np.sin(np.pi / MAGNET_BLOCKS_PER_PERIOD)
        * (1 - np.exp(-2 * np.pi * MAGNTE_BLOCK_HEIGHT_MM / undulator_period_mm))
    )


def calculate_gap_i09_hu(
    photon_energy_kev: float,
    look_up_table: dict[int, np.ndarray],
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

    _validate_order(order, look_up_table)
    gamma = _calculate_gamma(look_up_table, order)

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
    undulator_parameter_max = _calculate_undulator_parameter_max(
        look_up_table[order][MAGNET_FIELD_COLUMN], undulator_period_mm
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


def calculate_energy_i09_hu(
    gap: float,
    look_up_table: dict[int, "np.ndarray"],
    order: int = 1,
    gap_offset: float = 0.0,
    undulator_period_mm: int = 27,
) -> float:
    """
    Calculate the photon energy produced by the undulator at a given gap and harmonic order.
    Reverse of the calculate_gap_i09_hu function.

    Args:
        gap (float): Undulator gap in millimeters.
        look_up_table (dict[int, np.ndarray]): Lookup table containing undulator and beamline parameters for each harmonic order.
        order (int, optional): Harmonic order for which to calculate the energy. Defaults to 1.
        gap_offset (float, optional): Additional gap offset to apply (in mm). Defaults to 0.0.
        undulator_period_mm (int, optional): Undulator period in mm. Defaults to 27.

    Returns:
        float: Calculated photon energy in keV.
    """
    _validate_order(order, look_up_table)

    gamma = _calculate_gamma(look_up_table, order)
    undulator_parameter_max = _calculate_undulator_parameter_max(
        look_up_table[order][MAGNET_FIELD_COLUMN], undulator_period_mm
    )

    undulator_parameter = undulator_parameter_max / np.exp(
        (gap - look_up_table[order][GAP_OFFSET_COLUMN] - gap_offset)
        / (undulator_period_mm / np.pi)
    )
    energy_kev = (
        4.959368e-6
        * order
        * np.square(gamma)
        / (undulator_period_mm * (np.square(undulator_parameter) + 2))
    )
    return energy_kev
