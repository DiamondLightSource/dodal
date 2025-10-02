import numpy as np
from bluesky.protocols import Locatable, Location, Movable
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    soft_signal_r_and_setter,
    soft_signal_rw,
)

from dodal.devices.baton import Baton
from dodal.devices.undulator import (
    STATUS_TIMEOUT_S,
    UndulatorBase,
)
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
        LOGGER.debug(f"Loaded lookup table:\n {lut_dict}")
    return lut_dict


def calculate_gap_hu(
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
        raise ValueError("diffraction parameter squared must be positive!")
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
    # undulator_parameter = undulator_parameter_max*exp(-pi*gap/lambda_u) for gap gives:
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


class UndulatorOrder(StandardReadable, Locatable[int]):
    """
    Represents the order of an undulator, providing mechanisms to read, set, and validate the order value
    against a lookup table loaded from a file.

    """

    def __init__(self, id_gap_lookup_table_path: str, name: str = "") -> None:
        """
        Args:
            id_gap_lookup_table_path (str): Path to the lookup table file.
            name: Name for device. Defaults to ""
        """
        self.id_gap_lookup_table_path = id_gap_lookup_table_path
        with self.add_children_as_readables():
            self._order = soft_signal_rw(int, initial_value=3)
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: int):
        await self._check_order_valid(value)
        await self._order.set(value)

    async def _check_order_valid(self, value: int):
        self._lut_dict: dict = await get_hu_lut_as_dict(self.id_gap_lookup_table_path)
        LOGGER.debug(f"Loaded lookup table: {self._lut_dict}")
        if value not in self._lut_dict.keys():
            raise ValueError(
                f"Order {value} not found in lookup table, must be in {[int(key) for key in self._lut_dict.keys()]}"
            )

    async def locate(self) -> Location[int]:
        return await self._order.locate()


class HardUndulator(UndulatorBase, Movable[float]):
    """
    An Undulator-type insertion device, used to control photon emission at a
    given beam energy.

    This class extends Undulator and adds an order(harmonics) parameter. In addition there are gap_offset
    to allow for small adjustments to the gap and an undulator_period soft signals.
    """

    def __init__(
        self,
        prefix: str,
        order: UndulatorOrder,
        poles: int | None = None,
        undulator_period: int | None = None,
        length: float | None = None,
        baton: Baton | None = None,
        name: str = "",
    ) -> None:
        """Constructor

        Args:
            prefix: PV prefix
            order: UndulatorOrder object to set/get undulator order
            poles: Number of magnetic poles built into the undulator
            length: Length of the undulator in meters
            undulator_period: undulator period in mm
            baton: Baton
            name: Name for device. Defaults to ""
        """
        self.order = Reference(order)
        self.add_readables([self.order()])

        with self.add_children_as_readables():
            self.gap_offset, _ = soft_signal_r_and_setter(float, initial_value=0.0)

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            if undulator_period is not None:
                self.undulator_period, _ = soft_signal_r_and_setter(
                    int, initial_value=undulator_period
                )
            else:
                self.undulator_period = None

            if poles is not None:
                self.poles, _ = soft_signal_r_and_setter(int, initial_value=poles)
            else:
                self.poles = None

            if length is not None:
                self.length, _ = soft_signal_r_and_setter(float, initial_value=length)
            else:
                self.length = None

        super().__init__(prefix=prefix, baton=baton, name=name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        """
        Set the undulator gap to a given value in mm.

        Args:
            value: target gap in mm
        """
        await self.raise_if_not_enabled()  # Check access
        if await self.check_gap_within_threshold(value):
            LOGGER.debug(
                "Gap is already in the correct place, no need to ask it to move"
            )
            return
        await self._set_undulator_gap(value)

    async def _set_undulator_gap(self, target_gap: float) -> None:
        commissioning_mode = await self._is_commissioning_mode_enabled()
        if not commissioning_mode:
            await self.gap_motor.set(
                target_gap,
                timeout=STATUS_TIMEOUT_S,
            )
        else:
            LOGGER.warning("In test mode, not moving ID gap")
