import asyncio

from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, Device, DeviceMock, DeviceVector
from ophyd_async.epics.core import epics_signal_rw

from dodal.device_manager import DEFAULT_TIMEOUT
from dodal.devices.insertion_device import (
    EnergyCoverage,
    EnergyMotorLookup,
    LookupTable,
    Pol,
)
from dodal.log import LOGGER

ROW_PHASE_CIRCULAR = 15.0
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
DEFAULT_POLY1D_PARAMETERS = {
    Pol.LH: [0],
    Pol.LV: [MAXIMUM_ROW_PHASE_MOTOR_POSITION],
    Pol.PC: [ROW_PHASE_CIRCULAR],
    Pol.PC3: [ROW_PHASE_CIRCULAR],
    Pol.NC: [-ROW_PHASE_CIRCULAR],
    Pol.NC3: [-ROW_PHASE_CIRCULAR],
}


class I06EpicsPolynomialDevice(Device, Triggerable):
    def __init__(
        self,
        prefix: str,
        max_energy: float = 2200,
        min_energy: float = 70,
        phase_poly_params: dict[Pol, list[float]] = DEFAULT_POLY1D_PARAMETERS,
        name: str = "",
    ) -> None:
        # Define mapping of polarization to PV suffix
        self._pol_map = {
            Pol.LH: "HZ",
            Pol.LV: "VT",
            Pol.PC: "PC",
            Pol.NC: "NC",
            Pol.PC3: "PC:HAR3",
            Pol.NC3: "NC:HAR3",
        }
        self._inv_pol_map = {
            Pol.LH: "BHZ",
            Pol.LV: "BVT",
            Pol.PC: "BPC",
            Pol.NC: "BNC",
            Pol.PC3: "BPC:HAR3",
            Pol.NC3: "BNC:HAR3",
        }
        self.param_dict = {}
        self.inv_param_dict = {}
        self.min_energy = min_energy
        self.max_energy = max_energy
        self.phase_poly_params = phase_poly_params
        # Initialize DeviceVectors
        for pol, suffix in self._inv_pol_map.items():
            attr_name = f"{pol.name.lower()}_inverse_params"
            setattr(self, attr_name, self._make_params(f"{prefix}{suffix}"))
            self.inv_param_dict[pol] = getattr(self, attr_name)

        for pol, suffix in self._pol_map.items():
            attr_name = f"{pol.name.lower()}_params"
            setattr(self, attr_name, self._make_params(f"{prefix}{suffix}"))
            self.param_dict[pol] = getattr(self, attr_name)
        self.energy_gap_motor_lookup = EnergyMotorLookup()
        self.energy_phase_motor_lookup = EnergyMotorLookup()
        self.gap_motor_energy_lookup = EnergyMotorLookup()
        super().__init__(name=name)

    def _make_params(self, pv_prefix: str) -> DeviceVector:
        return DeviceVector(
            {
                i: epics_signal_rw(float, read_pv=f"{pv_prefix}:C{i}")
                for i in range(12, 0, -1)
            }
        )

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        """Triggering this device will update the lookup tables with the current PV values."""
        await self.update_lookup()

    async def _get_table_entries(
        self,
        param_dict: dict[Pol, DeviceVector] | dict[Pol, list[float]],
        min_energy: float,
        max_energy: float,
    ) -> dict[Pol, EnergyCoverage]:
        entries = {}
        for pol, vector in param_dict.items():
            if isinstance(vector, DeviceVector):
                coeffs = await asyncio.gather(*(p.get_value() for p in vector.values()))
            else:
                coeffs = vector
            entries[pol] = EnergyCoverage.generate(
                min_energies=[min_energy],
                max_energies=[max_energy],
                poly1d_params=[coeffs],
            )
        return entries

    async def update_lookup(self) -> None:
        # Update gap lookup table
        energy_entries = await self._get_table_entries(
            self.param_dict, self.min_energy, self.max_energy
        )
        self.energy_gap_motor_lookup = EnergyMotorLookup(LookupTable(energy_entries))
        # find gap range from energy range
        min_gap = self.energy_gap_motor_lookup.find_value_in_lookup_table(
            value=self.max_energy, pol=Pol.LH
        )
        max_gap = self.energy_gap_motor_lookup.find_value_in_lookup_table(
            value=self.min_energy, pol=Pol.LH
        )
        # Update gap inverse lookup table
        inv_energy_entries = await self._get_table_entries(
            self.inv_param_dict, max_energy=max_gap, min_energy=min_gap
        )
        self.gap_motor_energy_lookup = EnergyMotorLookup(
            LookupTable(inv_energy_entries)
        )
        # Update phase lookup table
        energy_entries = await self._get_table_entries(
            self.phase_poly_params, max_energy=max_gap, min_energy=min_gap
        )
        self.energy_phase_motor_lookup = EnergyMotorLookup(LookupTable(energy_entries))
        LOGGER.info("Updating lookup tables with new values from EPICS.")

    async def connect(
        self,
        mock: bool | DeviceMock = False,
        timeout: float = DEFAULT_TIMEOUT,
        force_reconnect: bool = False,
    ) -> None:
        await super().connect(
            mock=mock, timeout=timeout, force_reconnect=force_reconnect
        )
        # Highjack connect to update lookup tables on connection.
        await self.update_lookup()
