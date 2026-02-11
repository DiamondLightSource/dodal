from asyncio import gather
from typing import Any, Protocol

from bluesky.protocols import Locatable, Location, Movable
from daq_config_server.client import ConfigServer
from daq_config_server.models.converters.lookup_tables import GenericLookupTable
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    derived_signal_rw,
    soft_signal_rw,
)

from dodal.devices.common_dcm import DoubleCrystalMonochromatorBase
from dodal.devices.undulator import UndulatorInMm, UndulatorOrder


class LookUpTableProvider(Protocol):
    def get_look_up_table(self, *args, **kwargs) -> Any:
        """Protocol to provide lookup table data."""
        ...


class EnergyGapConvertor(Protocol):
    def __call__(
        self, look_up_table: GenericLookupTable, value: float, order: int
    ) -> float:
        """Protocol to provide value conversion using lookup table provider."""
        ...


class I09HardLutProvider(LookUpTableProvider):
    def __init__(self, config_server: ConfigServer, filepath: str) -> None:
        self.config_server = config_server
        self.filepath = filepath

    def get_look_up_table(self) -> GenericLookupTable:
        self._lut: GenericLookupTable = self.config_server.get_file_contents(
            self.filepath,
            desired_return_type=GenericLookupTable,
            reset_cached_result=True,
        )
        return self._lut


class HardInsertionDeviceEnergy(StandardReadable, Movable[float]):
    """Compound device to link hard x-ray undulator gap and order to photon energy.
    Setting the energy adjusts the undulator gap accordingly.
    """

    def __init__(
        self,
        undulator_order: UndulatorOrder,
        undulator: UndulatorInMm,
        lut_provider: LookUpTableProvider,
        gap_to_energy_func: EnergyGapConvertor,
        energy_to_gap_func: EnergyGapConvertor,
        name: str = "",
    ) -> None:
        self._undulator_order_ref = Reference(undulator_order)
        self._undulator_ref = Reference(undulator)
        self._lut_provider = lut_provider
        self.gap_to_energy_func = gap_to_energy_func
        self.energy_to_gap_func = energy_to_gap_func

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
        _lookup_table = self._lut_provider.get_look_up_table()
        return self.gap_to_energy_func(_lookup_table, current_gap, current_order)

    async def _set_energy(self, energy: float) -> None:
        current_order = await self._undulator_order_ref().value.get_value()
        _lookup_table = self._lut_provider.get_look_up_table()
        target_gap = self.energy_to_gap_func(_lookup_table, energy, current_order)
        await self._undulator_ref().set(target_gap)

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        self.energy_demand.set(value)
        await self.energy.set(value)


class HardEnergy(StandardReadable, Locatable[float]):
    """Energy compound device that provides combined change of both DCM energy and
    undulator gap accordingly.
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
