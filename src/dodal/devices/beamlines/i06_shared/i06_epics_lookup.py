import asyncio

from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, Device, DeviceMock, DeviceVector
from ophyd_async.epics.core import epics_signal_rw

from dodal.device_manager import DEFAULT_TIMEOUT
from dodal.devices.insertion_device import (
    MAXIMUM_GAP_MOTOR_POSITION,
    MAXIMUM_ROW_PHASE_MOTOR_POSITION,
    EnergyCoverage,
    EnergyMotorLookup,
    LookupTable,
    Pol,
)
from dodal.log import LOGGER

MINIMUM_GAP_MOTOR_POSITION = 15
ROW_PHASE_CIRCULAR = 15.0
DEFAULT_POLY1D_PARAMETERS = {
    Pol.LH: [0],
    Pol.LV: [MAXIMUM_ROW_PHASE_MOTOR_POSITION],
    Pol.PC: [ROW_PHASE_CIRCULAR],
    Pol.PC3: [ROW_PHASE_CIRCULAR],
    Pol.NC: [-ROW_PHASE_CIRCULAR],
    Pol.NC3: [-ROW_PHASE_CIRCULAR],
}


class I06EpicsPolynomialDevice(Device, Triggerable):
    """A specialized Insertion Device for the I06 beamline that dynamically synchronizes
    lookup tables with polynomial coefficients stored in EPICS PVs.

    This device reads coefficients (C0 through C12) for multiple polarizations to
    construct mappings between Energy, Gap, and Phase. It supports both forward
    (Energy -> Gap) and inverse (Gap -> Energy) lookups, as well as phase calculations.

    The device implements the `Triggerable` protocol, allowing the physics tables
    to be refreshed during a Bluesky plan via `yield from bps.trigger(device)`.

    Args:
        prefix (str): The EPICS prefix for the polynomial coefficient PVs.
        max_energy (float, optional): The maximum operating energy in eV. Defaults to 2200.
        min_energy (float, optional): The minimum operating energy in eV. Defaults to 70.
        phase_poly_params (dict[Pol, list[float]], optional): Static polynomial
            parameters for phase calculation. Defaults to DEFAULT_POLY1D_PARAMETERS.
        name (str, optional): The name of the device for Bluesky/Ophyd.

    Attributes:
        energy_gap_motor_lookup (EnergyMotorLookup): Mapping for Energy -> Gap.
        energy_phase_motor_lookup (EnergyMotorLookup): Mapping for Energy -> Phase.
        gap_motor_energy_lookup (EnergyMotorLookup): Mapping for Gap -> Energy.
        param_dict (dict[Pol, DeviceVector]): Dictionary of forward polynomial signals.
        inv_param_dict (dict[Pol, DeviceVector]): Dictionary of inverse polynomial signals.
    """

    def __init__(
        self,
        prefix: str,
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

        self.energy_gap_motor_lookup = EpicsPolynomialEnergyMotorLookup(
            prefix=prefix, max_value=2200, min_value=70, poly_params=self._pol_map
        )
        self.energy_phase_motor_lookup = EpicsPolynomialEnergyMotorLookup(
            prefix=prefix,
            max_value=2200,
            min_value=70,
        )
        self.gap_motor_energy_lookup = EpicsPolynomialEnergyMotorLookup(
            prefix=prefix,
            max_value=20,
            min_value=MAXIMUM_GAP_MOTOR_POSITION,
            poly_params=self._inv_pol_map,
        )
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        """Triggering this device will update the lookup tables with the current PV values."""
        await asyncio.gather(
            self.energy_gap_motor_lookup.update_lookup(),
            self.energy_phase_motor_lookup.update_lookup(),
            self.gap_motor_energy_lookup.update_lookup(),
        )


class EpicsPolynomialEnergyMotorLookup(Device, Triggerable, EnergyMotorLookup):
    """A specialized Insertion Device for the I06 beamline that dynamically synchronizes
    lookup tables with polynomial coefficients stored in EPICS PVs.

    This device reads coefficients (C0 through C12) for multiple polarizations to
    construct mappings between Energy, Gap, and Phase. It supports both forward
    (Energy -> Gap) and inverse (Gap -> Energy) lookups, as well as phase calculations.

    The device implements the `Triggerable` protocol, allowing the physics tables
    to be refreshed during a Bluesky plan via `yield from bps.trigger(device)`.

    Args:
        prefix (str): The EPICS prefix for the polynomial coefficient PVs.
        max_energy (float, optional): The maximum operating energy in eV. Defaults to 2200.
        min_energy (float, optional): The minimum operating energy in eV. Defaults to 70.
        phase_poly_params (dict[Pol, list[float]], optional): Static polynomial
            parameters for phase calculation. Defaults to DEFAULT_POLY1D_PARAMETERS.
        name (str, optional): The name of the device for Bluesky/Ophyd.

    Attributes:
        energy_gap_motor_lookup (EnergyMotorLookup): Mapping for Energy -> Gap.
        energy_phase_motor_lookup (EnergyMotorLookup): Mapping for Energy -> Phase.
        gap_motor_energy_lookup (EnergyMotorLookup): Mapping for Gap -> Energy.
        param_dict (dict[Pol, DeviceVector]): Dictionary of forward polynomial signals.
        inv_param_dict (dict[Pol, DeviceVector]): Dictionary of inverse polynomial signals.
    """

    def __init__(
        self,
        prefix: str,
        max_value: float,
        min_value: float,
        poly_params: dict[Pol, list[float]]
        | dict[Pol, str] = DEFAULT_POLY1D_PARAMETERS,
        name: str = "",
    ) -> None:
        self.param_dict = {}
        self.min_value = min_value
        self.max_value = max_value
        for pol, suffix in poly_params.items():
            if isinstance(suffix, str):
                attr_name = f"{pol.name.lower()}_params"
                setattr(
                    self,
                    attr_name,
                    self._make_params(
                        pv_prefix=f"{prefix}{suffix}",
                        start=12,
                        end=0,
                    ),
                )
                self.param_dict[pol] = getattr(self, attr_name)
            else:
                self.param_dict[pol] = poly_params[pol]
        super().__init__(name=name)

    def _make_params(
        self, pv_prefix: str, start: int = 12, end: int = 0
    ) -> DeviceVector:
        return DeviceVector(
            {
                i: epics_signal_rw(float, read_pv=f"{pv_prefix}:C{i}")
                for i in range(start, end, -1)
            }
        )

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        """Triggering this device will update the lookup tables with the current PV values."""
        await self.update_lookup()

    async def _get_table_entries(
        self,
        param_dict: dict[Pol, DeviceVector] | dict[Pol, list[float]],
        min_value: float,
        max_value: float,
    ) -> dict[Pol, EnergyCoverage]:
        entries = {}
        for pol, vector in param_dict.items():
            if isinstance(vector, DeviceVector):
                coeffs = await asyncio.gather(*(p.get_value() for p in vector.values()))
            else:
                coeffs = vector
            entries[pol] = EnergyCoverage.generate(
                min_energies=[min_value],
                max_energies=[max_value],
                poly1d_params=[coeffs],
            )
        return entries

    async def update_lookup(self) -> None:
        # Update gap lookup table
        energy_entries = await self._get_table_entries(
            self.param_dict, self.min_value, self.max_value
        )
        self.lut = LookupTable(energy_entries)

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
