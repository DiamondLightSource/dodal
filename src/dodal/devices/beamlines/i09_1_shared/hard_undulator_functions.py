import numpy as np
from daq_config_server.client import ConfigServer
from daq_config_server.models.converters.lookup_tables import GenericLookupTable

from dodal.devices.beamlines.i09_1_shared.hard_energy import LookUpTableProvider
from dodal.log import LOGGER

# Physics constants
ELECTRON_REST_ENERGY_MEV = 0.510999

# Column names in the lookup table
HARMONICS_COLUMN_NAME = "order"
RING_ENERGY_COLUMN_NAME = "ring_energy_gev"
MAGNET_FIELD_COLUMN_NAME = "magnetic_field_t"
MIN_ENERGY_COLUMN_NAME = "energy_min_ev"
MAX_ENERGY_COLUMN_NAME = "energy_max_ev"
MIN_GAP_COLUMN_NAME = "gap_min_mm"
MAX_GAP_COLUMN_NAME = "gap_max_mm"
GAP_OFFSET_COLUMN_NAME = "gap_offset_mm"
I09_HU_UNDULATOR_LUT_COLUMN_NAMES = [
    HARMONICS_COLUMN_NAME,
    RING_ENERGY_COLUMN_NAME,
    MAGNET_FIELD_COLUMN_NAME,
    MIN_ENERGY_COLUMN_NAME,
    MAX_ENERGY_COLUMN_NAME,
    MIN_GAP_COLUMN_NAME,
    MAX_GAP_COLUMN_NAME,
    GAP_OFFSET_COLUMN_NAME,
]
MAGNET_BLOCKS_PER_PERIOD = 4
MAGNET_BLOCK_HEIGHT_MM = 16


class I09HardLutProvider(LookUpTableProvider):
    def __init__(self, config_server: ConfigServer, filepath: str) -> None:
        self.config_server = config_server
        self.filepath = filepath

    def get_look_up_table(self) -> GenericLookupTable:
        self._lut = self.config_server.get_file_contents(
            self.filepath,
            desired_return_type=GenericLookupTable,
            reset_cached_result=True,
        )
        return self._lut


def _validate_order(look_up_table: GenericLookupTable, order: int) -> None:
    """Validate that the harmonic order exists in the lookup table."""
    order_column_index = look_up_table.get_column_names().index(HARMONICS_COLUMN_NAME)
    if order not in look_up_table.columns[order_column_index]:
        raise ValueError(f"Order parameter {order} not found in lookup table")


def _validate_energy_in_range(
    look_up_table: GenericLookupTable,
    energy: float,
    order: int,
) -> None:
    """Check if the requested energy is within the allowed range for the current harmonic order."""
    min_energy = look_up_table.get_value(
        HARMONICS_COLUMN_NAME, order, MIN_ENERGY_COLUMN_NAME
    )
    max_energy = look_up_table.get_value(
        HARMONICS_COLUMN_NAME, order, MAX_ENERGY_COLUMN_NAME
    )
    if not (min_energy <= energy <= max_energy):
        raise ValueError(
            f"Requested energy {energy} keV is out of range for harmonic {order}: "
            f"[{min_energy}, {max_energy}] keV"
        )


def _calculate_gamma(look_up_table: GenericLookupTable, order: int) -> float:
    """Calculate the Lorentz factor gamma from the lookup table."""
    ring_energy_gev = look_up_table.get_value(
        HARMONICS_COLUMN_NAME, order, "ring_energy_gev"
    )
    return 1000 * ring_energy_gev / ELECTRON_REST_ENERGY_MEV


def _calculate_undulator_parameter_max(
    magnet_field: float, undulator_period_mm: int
) -> float:
    """Calculate the maximum undulator parameter."""
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
        * (1 - np.exp(-2 * np.pi * MAGNET_BLOCK_HEIGHT_MM / undulator_period_mm))
    )


def calculate_gap_i09_hu(
    lut: LookUpTableProvider,
    value: float,
    order: int = 1,
) -> float:
    """Calculate the undulator gap required to produce a given energy at a given harmonic order.
    This algorithm was provided by the I09 beamline scientists, and is based on the physics of undulator radiation.
    https://cxro.lbl.gov//PDF/X-Ray-Data-Booklet.pdf.

    Args:
        value (float): Requested photon energy in keV.
        lut (LookUpTableProvider): Lookup table provider to get beamline parameters for each harmonic order.
        order (int, optional): Harmonic order for which to calculate the gap. Defaults to 1.

    Returns:
        float: Calculated undulator gap in millimeters.
    """
    gap_offset: float = 0.0
    undulator_period_mm: int = 27
    look_up_table: GenericLookupTable = lut.get_look_up_table()

    # Validate inputs
    _validate_order(look_up_table, order)
    _validate_energy_in_range(look_up_table, value, order)

    gamma = _calculate_gamma(look_up_table, order)

    # Constructive interference of radiation emitted at different poles
    # lamda = (lambda_u/2*gamma^2)*(1+K^2/2 + gamma^2*theta^2)/n for n=1,2,3...
    # theta is the observation angle, assumed to be 0 here.
    # Rearranging for K (the undulator parameter, related to magnetic field and gap)
    # gives K^2 = 2*((2*n*gamma^2*lamda/lambda_u)-1)

    undulator_parameter_sqr = (
        4.959368e-6 * (order * gamma * gamma / (undulator_period_mm * value)) - 2
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
        look_up_table.get_value(HARMONICS_COLUMN_NAME, order, MAGNET_FIELD_COLUMN_NAME),
        undulator_period_mm,
    )

    # Finnaly, rearranging the equation:
    # undulator_parameter = undulator_parameter_max*exp(-pi*gap/lambda_u) for gap gives
    gap = (
        (undulator_period_mm / np.pi)
        * np.log(undulator_parameter_max / undulator_parameter)
        + look_up_table.get_value(HARMONICS_COLUMN_NAME, order, GAP_OFFSET_COLUMN_NAME)
        + gap_offset
    )
    LOGGER.debug(f"Calculated gap is {gap}mm for energy {value}keV at order {order}")

    return gap


def calculate_energy_i09_hu(
    lut: LookUpTableProvider,
    value: float,
    order: int = 1,
) -> float:
    """Calculate the photon energy produced by the undulator at a given gap and harmonic order.
    Reverse of the calculate_gap_i09_hu function.

    Args:
        value (float): Undulator gap in millimeters.
        lut (LookUpTableProvider): Lookup table provider to get beamline parameters for each harmonic order.
        order (int, optional): Harmonic order for which to calculate the energy. Defaults to 1.

    Returns:
        float: Calculated photon energy in keV.
    """
    gap_offset: float = 0.0
    undulator_period_mm: int = 27

    look_up_table: GenericLookupTable = lut.get_look_up_table()
    _validate_order(look_up_table, order)

    gamma = _calculate_gamma(look_up_table, order)
    undulator_parameter_max = _calculate_undulator_parameter_max(
        look_up_table.get_value(HARMONICS_COLUMN_NAME, order, MAGNET_FIELD_COLUMN_NAME),
        undulator_period_mm,
    )

    undulator_parameter = undulator_parameter_max / np.exp(
        (
            value
            - look_up_table.get_value(
                HARMONICS_COLUMN_NAME, order, GAP_OFFSET_COLUMN_NAME
            )
            - gap_offset
        )
        / (undulator_period_mm / np.pi)
    )
    energy_kev = (
        4.959368e-6
        * order
        * np.square(gamma)
        / (undulator_period_mm * (np.square(undulator_parameter) + 2))
    )
    return energy_kev
