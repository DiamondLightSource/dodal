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

MAXE = 1700
MINE = 100


class I06EpicsPolynomailDevice(Device, Movable):
    def __init__(self, prefix: str, name: str = "") -> None:
        self.lh_polyn_params = DeviceVector(
            {
                i: epics_signal_rw(float, read_pv=f"{prefix}HZ:C{i}")
                for i in range(1, 13)
            }
        )
        self.lv_polyn_params = DeviceVector(
            {
                i: epics_signal_rw(float, read_pv=f"{prefix}VT:C{i}")
                for i in range(1, 13)
            }
        )
        self.pc_polyn_params = DeviceVector(
            {
                i: epics_signal_rw(float, read_pv=f"{prefix}PC:C{i}")
                for i in range(1, 13)
            }
        )
        self.nc_polyn_params = DeviceVector(
            {
                i: epics_signal_rw(float, read_pv=f"{prefix}NC:C{i}")
                for i in range(1, 13)
            }
        )
        self.pc_har3_polyn_params = DeviceVector(
            {
                i: epics_signal_rw(float, read_pv=f"{prefix}PC:HAR3:C{i}")
                for i in range(1, 13)
            }
        )
        self.nc_har3_polyn_params = DeviceVector(
            {
                i: epics_signal_rw(float, read_pv=f"{prefix}NC:HAR3:C{i}")
                for i in range(1, 13)
            }
        )
        self.lut: EnergyMotorLookup = EnergyMotorLookup()
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        lh = [await param.get_value() for param in self.lh_polyn_params.values()]
        lv = [await param.get_value() for param in self.lv_polyn_params.values()]
        pc = [await param.get_value() for param in self.pc_polyn_params.values()]
        nc = [await param.get_value() for param in self.nc_polyn_params.values()]
        # pc_har3 = [
        #     await param.get_value() for param in self.pc_har3_polyn_params.values()
        # ]
        # nc_har3 = [
        #     await param.get_value() for param in self.nc_har3_polyn_params.values()
        # ]
        energy_entries = {
            Pol.LH: EnergyCoverage.generate(
                min_energies=[MINE],
                max_energies=[MAXE],
                poly1d_params=[lh],
            ),
            Pol.LV: EnergyCoverage.generate(
                min_energies=[MINE],
                max_energies=[MAXE],
                poly1d_params=[lv],
            ),
            Pol.PC: EnergyCoverage.generate(
                min_energies=[MINE],
                max_energies=[MAXE],
                poly1d_params=[pc],
            ),
            Pol.NC: EnergyCoverage.generate(
                min_energies=[MINE],
                max_energies=[MAXE],
                poly1d_params=[nc],
            ),
            # Pol.PC_HAR3: EnergyCoverage.generate(
            #     min_energies=[MINE],
            #     max_energies=[MAXE],
            #     poly1d_params=[pc_har3],
            # ),
            # Pol.NC_HAR3: EnergyCoverage.generate(
            #     min_energies=[MINE],
            #     max_energies=[MAXE],
            #     poly1d_params=[nc_har3],
            # ),
        }
        self.lut = EnergyMotorLookup(LookupTable(energy_entries))

    async def connect(
        self,
        mock: bool | DeviceMock = False,
        timeout: float = DEFAULT_TIMEOUT,
        force_reconnect: bool = False,
    ) -> None:
        await super().connect(
            mock=mock, timeout=timeout, force_reconnect=force_reconnect
        )
        await self.set(0)  # set to trigger reading polynomial coefficients from EPICS
