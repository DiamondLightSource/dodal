from bluesky.protocols import Movable
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

MAXE = 1700
MINE = 100


class I06EpicsPolynomialDevice(Device, Movable):
    def __init__(self, prefix: str, name: str = "") -> None:
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

        # Initialize DeviceVectors
        for pol, suffix in self._inv_pol_map.items():
            attr_name = f"{pol.name.lower()}_inverse_params"
            setattr(self, attr_name, self._make_params(f"{prefix}{suffix}"))
            self.inv_param_dict[pol] = getattr(self, attr_name)

        for pol, suffix in self._pol_map.items():
            attr_name = f"{pol.name.lower()}_params"
            setattr(self, attr_name, self._make_params(f"{prefix}{suffix}"))
            self.param_dict[pol] = getattr(self, attr_name)
        self.energy_motor_lookup = EnergyMotorLookup()
        self.motor_energy_lookup = EnergyMotorLookup()
        super().__init__(name=name)

    def _make_params(self, pv_prefix: str) -> DeviceVector:
        return DeviceVector(
            {
                i: epics_signal_rw(float, read_pv=f"{pv_prefix}:C{i}")
                for i in range(12, 0, -1)
            }
        )

    async def _get_table_entries(
        self,
        param_dict: dict[Pol, DeviceVector],
        max_energy: float = MAXE,
        min_energy: float = MINE,
    ) -> dict[Pol, EnergyCoverage]:
        entries = {}
        for pol, vector in param_dict.items():
            coeffs = [await p.get_value() for p in vector.values()]
            entries[pol] = EnergyCoverage.generate(
                min_energies=[min_energy],
                max_energies=[max_energy],
                poly1d_params=[coeffs],
            )
        return entries

    @AsyncStatus.wrap
    async def set(self, update: bool = True) -> None:
        if update:
            energy_entries = await self._get_table_entries(self.param_dict)
            self.energy_motor_lookup = EnergyMotorLookup(LookupTable(energy_entries))

            inv_energy_entries = await self._get_table_entries(
                self.inv_param_dict, max_energy=2000, min_energy=-2000
            )
            self.motor_energy_lookup = EnergyMotorLookup(
                LookupTable(inv_energy_entries)
            )
        else:
            LOGGER.info("Not updating lookup tables as update=False")

    async def connect(
        self,
        mock: bool | DeviceMock = False,
        timeout: float = DEFAULT_TIMEOUT,
        force_reconnect: bool = False,
    ) -> None:
        await super().connect(
            mock=mock, timeout=timeout, force_reconnect=force_reconnect
        )
        # highjack connect to update lookup tables on connection.
        await self.set(update=True)
