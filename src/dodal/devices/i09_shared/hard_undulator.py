import numpy as np
from ophyd_async.core import (
    AsyncStatus,
    soft_signal_r_and_setter,
    soft_signal_rw,
)

from dodal.devices.undulator import Undulator
from dodal.devices.util.lookup_tables import energy_distance_table
from dodal.log import LOGGER

LUT_COMMENTS = ["#", "Units", "ScannableNames", "ScannableUnits"]


def _get_gap_for_energy_order(
    energy_kev: float,
    look_up_table: "np.ndarray",
    order: int = 1,
    gap_offset: float = 0.0,
    undulator_period: int = 27,
) -> float:
    M = 4
    h = 16
    me = 0.510999
    gamma = 1000 * look_up_table[order][1] / me
    k_squared = (
        4.959368e-6 * (order * gamma * gamma / (undulator_period * energy_kev)) - 2
    )
    if k_squared < 0:
        raise ValueError("k_squared must be positive!")
    K = np.sqrt(k_squared)
    A = (
        (2 * 0.0934 * undulator_period * look_up_table[order][2] * M / np.pi)
        * np.sin(np.pi / M)
        * (1 - np.exp(-2 * np.pi * h / undulator_period))
    )
    gap = (
        (undulator_period / np.pi) * np.log(A / K)
        + look_up_table[order][7]
        + gap_offset
    )
    LOGGER.debug(
        f"Calculated gap is {gap}mm for energy {energy_kev}keV at order {order}"
    )

    return gap


class HardUndulator(Undulator):
    """
    A Hard X-ray Undulator-type insertion device, used to control photon emission at a
    given beam energy.

    This class is currently identical to the base Undulator class, but exists to allow
    future specialisation for hard X-ray undulators if required.
    """

    def __init__(
        self,
        prefix: str,
        id_gap_lookup_table_path: str,
        name: str = "",
        poles: int | None = None,
        length: float | None = None,
    ) -> None:
        """Constructor

        Args:
            prefix: PV prefix
            id_gap_lookup_table_path: Path to lookup table for gap vs energy
            name (str, optional): Name for device. Defaults to ""
            poles (int): Number of magnetic poles built into the undulator
            length (float): Length of the undulator in meters.
        """
        with self.add_children_as_readables():
            # Additional signals specific to HardUndulator
            self.order_signal = soft_signal_rw(int, initial_value=3)
            self.undulator_period, _ = soft_signal_r_and_setter(int, initial_value=27)
            self.gap_offset, _ = soft_signal_r_and_setter(float, initial_value=0.0)

        super().__init__(
            prefix,
            id_gap_lookup_table_path=id_gap_lookup_table_path,
            name=name,
            poles=poles,
            length=length,
        )

    @AsyncStatus.wrap
    async def set(self, value: float, order: int = 3):
        """
        Set the undulator gap to a given energy in keV and harmonic order

        Args:
            value (float): energy in keV
            order (int): harmonic order, defaults to 3
        """
        await self.check_energy_limits(value, order)
        await self.order_signal.set(order)
        await self._set_undulator_gap(value)

    async def check_energy_limits(self, value: float, order: int):
        min_energy, max_energy = await self.get_min_max_energy_for_order(order)
        if value < min_energy or value > max_energy:
            raise ValueError(
                f"Energy {value}keV is out of range for order {order} in the lookup table"
            )

    async def _get_gap_to_match_energy(self, energy_kev: float) -> float:
        """
        Asynchronously calculates the undulator gap required to match a specified energy.

        Args:
            energy_kev (float): The target energy in keV for which the undulator gap should be matched.

        Returns:
            float: The calculated undulator gap value corresponding to the specified energy.

        Raises:
            ValueError: If the specified energy is outside the allowed limits.

        Notes:
            - This method checks if the energy is within valid limits before calculation.
            - The calculation uses a lookup table and considers the current undulator order, gap offset, and period.
        """
        await self.check_energy_limits(energy_kev, await self.order_signal.get_value())
        return _get_gap_for_energy_order(
            energy_kev,
            look_up_table=await energy_distance_table(
                self.id_gap_lookup_table_path, comments=LUT_COMMENTS
            ),
            order=await self.order_signal.get_value(),
            gap_offset=await self.gap_offset.get_value(),
            undulator_period=await self.undulator_period.get_value(),
        )

    async def get_min_max_energy_for_order(self, order: int) -> tuple[float, float]:
        """
        Get the minimum and maximum energies in keV for a given harmonic order from
        the lookup table

        Args:
            order (int): harmonic order
        Returns:
            tuple: (min energy, max energy) in keV
        """
        look_up_table = await energy_distance_table(
            self.id_gap_lookup_table_path, comments=LUT_COMMENTS
        )
        if order < 1 or order >= look_up_table.shape[0]:
            raise ValueError(
                f"Order {order} is out of range for the lookup table, must be between 1 and {look_up_table.shape[0] - 1}"
            )
        LOGGER.debug(
            f"Min and max energies for order {order} are {look_up_table[order][3]}keV and {look_up_table[order][4]}keV respectively"
        )
        return (look_up_table[order][3], look_up_table[order][4])
