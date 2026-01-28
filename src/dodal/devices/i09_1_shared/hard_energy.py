from asyncio import gather
from collections.abc import Callable

from bluesky.protocols import Locatable, Location, Movable
from numpy import ndarray
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_rw,
    soft_signal_rw,
)

from dodal.devices.common_dcm import DoubleCrystalMonochromatorBase
from dodal.devices.i09_1_shared.hard_undulator_functions import (
    MAX_ENERGY_COLUMN,
    MIN_ENERGY_COLUMN,
)
from dodal.devices.undulator import UndulatorInMm, UndulatorOrder


class HardInsertionDeviceEnergy(StandardReadable, Movable[float]):
    """
    Compound device to link hard x-ray undulator gap and order to photon energy.
    Setting the energy adjusts the undulator gap accordingly.
    """

    def __init__(
        self,
        undulator_order: UndulatorOrder,
        undulator: UndulatorInMm,
        lut: dict[int, ndarray],
        gap_to_energy_func: Callable[..., float],
        energy_to_gap_func: Callable[..., float],
        name: str = "",
    ) -> None:
        self._lut = lut
        self.gap_to_energy_func = gap_to_energy_func
        self.energy_to_gap_func = energy_to_gap_func
        self._undulator_order_ref = Reference(undulator_order)
        self._undulator_ref = Reference(undulator)

        self.add_readables([undulator_order, undulator.current_gap])
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.energy_demand = soft_signal_rw(float)
            self.energy = derived_signal_rw(
                raw_to_derived=self._read_energy,
                set_derived=self._set_energy,
                current_gap=self._undulator_ref().gap_motor.user_readback,
                current_order=self._undulator_order_ref().value,
                derived_units="keV",
            )
        super().__init__(name=name)

    def _read_energy(self, current_gap: float, current_order: int) -> float:
        return self.gap_to_energy_func(
            gap=current_gap,
            look_up_table=self._lut,
            order=current_order,
        )

    async def _set_energy(self, energy: float) -> None:
        current_order = await self._undulator_order_ref().value.get_value()
        min_energy, max_energy = self._lut[current_order][
            MIN_ENERGY_COLUMN : MAX_ENERGY_COLUMN + 1
        ]
        if not (min_energy <= energy <= max_energy):
            raise ValueError(
                f"Requested energy {energy} keV is out of range for harmonic {current_order}: "
                f"[{min_energy}, {max_energy}] keV"
            )

        target_gap = self.energy_to_gap_func(
            photon_energy_kev=energy, look_up_table=self._lut, order=current_order
        )
        await self._undulator_ref().set(target_gap)

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        self.energy_demand.set(value)
        await self.energy.set(value)


class HardEnergy(StandardReadable, Locatable[float]):
    """
    Energy compound device that provides combined change of both DCM energy and undulator gap accordingly.
    """

    def __init__(
        self,
        dcm: DoubleCrystalMonochromatorBase,
        undulator_energy: HardInsertionDeviceEnergy,
        name: str = "",
    ) -> None:
        self._dcm_ref = Reference(dcm)
        self._undulator_energy_ref = Reference(undulator_energy)
        self.add_readables([undulator_energy, dcm.energy_in_keV])
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        await gather(
            self._dcm_ref().energy_in_keV.set(value),
            self._undulator_energy_ref().set(value),
        )

    async def locate(self) -> Location[float]:
        return Location(
            setpoint=await self._dcm_ref().energy_in_keV.user_setpoint.get_value(),
            readback=await self._dcm_ref().energy_in_keV.user_readback.get_value(),
        )
