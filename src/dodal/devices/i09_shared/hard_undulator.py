import numpy as np
from ophyd_async.core import (
    AsyncStatus,
    soft_signal_r_and_setter,
    soft_signal_rw,
)

from dodal.devices.undulator import Undulator
from dodal.devices.util.lookup_tables import energy_distance_table
from dodal.log import LOGGER

LUT_COMMENTS = ["#"]
HU_SKIP_ROWS = 3


def calculate_gap(
    energy_kev: float,
    look_up_table: dict[int, "np.ndarray"],
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

    This class extends Undulator and adds specialisation for hard X-ray undulators.
    """

    def __init__(
        self,
        prefix: str,
        id_gap_lookup_table_path: str,
        name: str = "",
        poles: int | None = None,
        length: float | None = None,
    ) -> None:
        """
        Args:
            prefix: PV prefix
            id_gap_lookup_table_path: Path to lookup table for gap vs energy
            name: Name for device. Defaults to ""
            poles: Number of magnetic poles built into the undulator
            length: Length of the undulator in meters.
        """
        with self.add_children_as_readables():
            self.order = soft_signal_rw(int, initial_value=3)
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
    async def set(self, value: float):
        """
        Set the undulator gap to a given energy in keV and harmonic order.

        Args:
            value: energy in keV
        """
        _current_order = await self.order.get_value()
        await self.check_energy_limits(value, _current_order)
        await self._set_undulator_gap(value)

    async def set_order(self, order: int):
        """
        Set the undulator harmonic order.

        Args:
            order: harmonic order
        """
        await self._check_order_valid(order)
        await self.order.set(order)

    async def get_order(self) -> int:
        """
        Get the undulator harmonic order.
        Returns:
            order: harmonic order
        """
        return await self.order.get_value()

    async def check_energy_limits(self, value: float, order: int):
        """
        Asynchronously checks if the specified energy value is within the allowed limits for a given undulator order.

        Args:
            value (float): The energy value in keV to check.
            order (int): The undulator harmonic order for which to check the energy limits.

        Raises:
            ValueError: If the energy value is outside the allowed range for the specified order.
        """
        min_energy, max_energy = await self.get_min_max_energy_for_order(order)
        if not (min_energy <= value <= max_energy):
            raise ValueError(
                f"Energy {value}keV is out of range for order {order}: ({min_energy}-{max_energy} keV)"
            )

    async def _get_gap_to_match_energy(self, energy_kev: float) -> float:
        """
        Asynchronously calculates the undulator gap required to match a specified energy.

        Args:
            energy_kev: The target energy in keV.

        Returns:
            The calculated undulator gap value.

        Raises:
            ValueError: If the specified energy is outside the allowed limits.
        """
        _current_order = await self.order.get_value()
        await self.check_energy_limits(energy_kev, _current_order)
        return calculate_gap(
            energy_kev,
            look_up_table=self._cached_lookup_table,
            order=_current_order,
            gap_offset=await self.gap_offset.get_value(),
            undulator_period=await self.undulator_period.get_value(),
        )

    async def update_cached_lookup_table(self):
        """
        Force update of cached lookup table by reading lut file.

        Raises:
            RuntimeError: If the lookup table cannot be loaded.
        """
        _lookup_table: np.ndarray = await energy_distance_table(
            self.id_gap_lookup_table_path,
            comments=LUT_COMMENTS,
            skiprows=HU_SKIP_ROWS,
        )
        if _lookup_table.size == 0:
            raise RuntimeError(
                f"Failed to load lookup table from path {self.id_gap_lookup_table_path}"
            )

        # cache the lookup table as a dictionary keyed on the order
        self._cached_lookup_table = {}
        for i in range(_lookup_table.shape[0]):
            self._cached_lookup_table[_lookup_table[i][0]] = _lookup_table[i]

        LOGGER.debug(f"Loaded lookup table:\n{self._cached_lookup_table}")

    async def get_min_max_energy_for_order(self, order: int) -> tuple[float, float]:
        """
        Get the minimum and maximum energies in keV for a given harmonic order from
        the lookup table.

        Args:
            order: harmonic order

        Returns:
            (min energy, max energy) in keV
        """
        await self._check_order_valid(order)
        min_energy = self._cached_lookup_table[order][3]
        max_energy = self._cached_lookup_table[order][4]
        LOGGER.debug(
            f"Min and max energies for order {order} are {min_energy}keV and {max_energy}keV respectively"
        )
        return min_energy, max_energy

    async def _check_order_valid(self, order):
        if not hasattr(self, "_cached_lookup_table"):
            await self.update_cached_lookup_table()
        if order not in self._cached_lookup_table.keys():
            raise ValueError(
                f"Order {order} not found in lookup table, must be between {min(self._cached_lookup_table.keys())} and {max(self._cached_lookup_table.keys())}"
            )
