from asyncio import gather
from typing import Protocol

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


class EnergyGapConvertor(Protocol):
    def __call__(
        self, look_up_table: GenericLookupTable, value: float, order: int
    ) -> float:
        """Protocol for a function to provide value conversion using lookup table."""
        ...


class HardInsertionDeviceEnergy(StandardReadable, Movable[float]):
    """Compound device to control isertion device energy.

    This device link hard x-ray undulator gap and order to photon energy.
    Setting the energy adjusts the undulator gap accordingly.

    Attributes:
        energy_demand (SignalRW[float]): The energy value that the user wants to set.
        energy (SignalRW[float]): The actual energy of the insertion device.
    """

    def __init__(
        self,
        undulator_order: UndulatorOrder,
        undulator: UndulatorInMm,
        config_server: ConfigServer,
        filepath: str,
        gap_to_energy_func: EnergyGapConvertor,
        energy_to_gap_func: EnergyGapConvertor,
        name: str = "",
    ) -> None:
        """Initialize the HardInsertionDeviceEnergy device.

        Args:
            undulator_order (UndulatorOrder): undulator order device.
            undulator (UndulatorInMm): undulator device for gap control.
            config_server (ConfigServer): Config server client to retrieve the lookup table.
            filepath (str): File path to the lookup table on the config server.
            gap_to_energy_func (EnergyGapConvertor): Function to convert gap to energy using the lookup table.
            energy_to_gap_func (EnergyGapConvertor): Function to convert energy to gap using the lookup table.
            name (str, optional): Name for the device. Defaults to empty string.
        """
        self._undulator_order_ref = Reference(undulator_order)
        self._undulator_ref = Reference(undulator)
        self._config_server = config_server
        self._filepath = filepath
        self._gap_to_energy_func = gap_to_energy_func
        self._energy_to_gap_func = energy_to_gap_func

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
        _lookup_table = self.get_look_up_table()
        return self._gap_to_energy_func(
            look_up_table=_lookup_table, value=current_gap, order=current_order
        )

    async def _set_energy(self, value: float) -> None:
        current_order = await self._undulator_order_ref().value.get_value()
        _lookup_table = self.get_look_up_table()
        target_gap = self._energy_to_gap_func(_lookup_table, value, current_order)
        await self._undulator_ref().set(target_gap)

    def get_look_up_table(self) -> GenericLookupTable:
        self._lut: GenericLookupTable = self._config_server.get_file_contents(
            self._filepath,
            desired_return_type=GenericLookupTable,
            reset_cached_result=True,
        )
        return self._lut

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        self.energy_demand.set(value)
        await self.energy.set(value)


class HardEnergy(StandardReadable, Locatable[float]):
    """Compound energy device.

    This device changes both monochromator and insertion device energy.
    """

    def __init__(
        self,
        dcm: DoubleCrystalMonochromatorBase,
        undulator_energy: HardInsertionDeviceEnergy,
        name: str = "",
    ) -> None:
        """Initialize the HardEnergy device.

        Args:
            dcm (DoubleCrystalMonochromatorBase): Double crystal monochromator device.
            undulator_energy (HardInsertionDeviceEnergy): Hard insertion device control.
            name (str, optional): name for the device. Defaults to empty.
        """
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
