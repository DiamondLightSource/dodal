from collections.abc import Callable

import numpy as np
from bluesky.protocols import Locatable, Location
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadable,
    soft_signal_r_and_setter,
    soft_signal_rw,
)

from dodal.devices.undulator import Undulator
from dodal.devices.util.lookup_tables import energy_distance_table
from dodal.log import LOGGER

LUT_COMMENTS = ["#"]
HU_SKIP_ROWS = 3

# Electron rest energy in MeV
ELECTRON_REST_ENERGY_MEV = 0.510999

# Columns in the lookup table
RING_ENERGY_COLUMN = 1
MAGNET_FIELD_COLUMN = 2
MIN_ENERGY_COLUMN = 3
MAX_ENERGY_COLUMN = 4
GAP_OFFSET_COLUMN = 7


def calculate_gap_i09(
    photon_energy_kev: float,
    look_up_table: dict[int, "np.ndarray"],
    order: int = 1,
    gap_offset: float = 0.0,
    undulator_period: int = 27,
) -> float:
    """
    Calculate the undulator gap required to produce a given energy at a given harmonic order.
    This algorithm was provided by the I09 beamline scientists.
    """
    M = 4
    h = 16

    gamma = 1000 * look_up_table[order][RING_ENERGY_COLUMN] / ELECTRON_REST_ENERGY_MEV
    k_squared = (
        4.959368e-6 * (order * gamma * gamma / (undulator_period * photon_energy_kev))
        - 2
    )
    if k_squared < 0:
        raise ValueError("k_squared must be positive!")
    K = np.sqrt(k_squared)
    A = (
        (
            2
            * 0.0934
            * undulator_period
            * look_up_table[order][MAGNET_FIELD_COLUMN]
            * M
            / np.pi
        )
        * np.sin(np.pi / M)
        * (1 - np.exp(-2 * np.pi * h / undulator_period))
    )
    gap = (
        (undulator_period / np.pi) * np.log(A / K)
        + look_up_table[order][GAP_OFFSET_COLUMN]
        + gap_offset
    )
    LOGGER.debug(
        f"Calculated gap is {gap}mm for energy {photon_energy_kev}keV at order {order}"
    )

    return gap


class UndulatorOrder(StandardReadable, Locatable[int]):
    def __init__(self, id_gap_lookup_table_path: str, name="") -> None:
        self.id_gap_lookup_table_path = id_gap_lookup_table_path
        with self.add_children_as_readables():
            self._order = soft_signal_rw(int, initial_value=3)
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: int):
        await self._check_order_valid(value)
        await self._order.set(value)

    async def _check_order_valid(self, value: int):
        self._lookup_table: np.ndarray = await energy_distance_table(
            self.id_gap_lookup_table_path,
            comments=LUT_COMMENTS,
            skiprows=HU_SKIP_ROWS,
        )
        LOGGER.debug(f"Loaded lookup table: {self._lookup_table}")
        order_list = [int(row[0]) for row in self._lookup_table]
        if value not in order_list:
            raise ValueError(
                f"Order {value} not found in lookup table, must be in {order_list}"
            )

    async def locate(self) -> Location[int]:
        return await self._order.locate()


class HardUndulator(Undulator):
    """
    An Undulator-type insertion device, used to control photon emission at a
    given beam energy.

    This class extends Undulator and adds an order(harmonics) parameter.
    """

    def __init__(
        self,
        prefix: str,
        order: UndulatorOrder,
        id_gap_lookup_table_path: str,
        calculate_gap_function: Callable[..., float],
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
        self._cached_lookup_table: dict[int, np.ndarray] = {}
        self.calculate_gap = calculate_gap_function
        self.order = Reference(order)

        self.add_readables([self.order()])
        with self.add_children_as_readables():
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
        Set the undulator gap to a given energy in keV.

        Args:
            value: energy in keV
        """
        if self._cached_lookup_table == {}:
            await self._update_cached_lookup_table()
        await self._check_energy_limits(value)
        await self._set_undulator_gap(value)

    async def _check_energy_limits(self, value: float):
        """
        Asynchronously checks if the specified energy value is within the allowed limits for a given undulator order.

        Args:
            value (float): The energy value in keV to check.
        """
        _current_order = (await self.order().locate()).get("readback")
        min_energy = self._cached_lookup_table[_current_order][MIN_ENERGY_COLUMN]
        max_energy = self._cached_lookup_table[_current_order][MAX_ENERGY_COLUMN]
        LOGGER.debug(
            f"Min and max energies for order {_current_order} are {min_energy}keV and {max_energy}keV respectively"
        )
        if not (min_energy <= value <= max_energy):
            raise ValueError(
                f"Energy {value}keV is out of range for order {_current_order}: ({min_energy}-{max_energy} keV)"
            )

    async def _get_gap_to_match_energy(self, energy_kev: float) -> float:
        """
        Asynchronously calculates the undulator gap required to match a specified energy.

        Args:
            energy_kev: The target energy in keV.

        Returns:
            The calculated undulator gap value.
        """
        return self.calculate_gap(
            photon_energy_kev=energy_kev,
            look_up_table=self._cached_lookup_table,
            order=(await self.order().locate()).get("readback"),
            gap_offset=await self.gap_offset.get_value(),
            undulator_period=await self.undulator_period.get_value(),
        )

    async def _update_cached_lookup_table(self):
        """
        Force update of cached lookup table by reading lut file.
        Use cached version to avoid reading file multiple times during energy scans.
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
        self._cached_lookup_table.clear()
        for i in range(_lookup_table.shape[0]):
            self._cached_lookup_table[_lookup_table[i][0]] = _lookup_table[i]
        LOGGER.debug(f"Loaded lookup table:\n{self._cached_lookup_table}")
