import asyncio
from pathlib import Path

from bluesky.protocols import Triggerable
from daq_config_server import ConfigClient
from ophyd_async.core import AsyncStatus, Device, DeviceMock, DeviceVector
from ophyd_async.epics.core import epics_signal_rw

from dodal.device_manager import DEFAULT_TIMEOUT
from dodal.devices.insertion_device.enum import Pol
from dodal.devices.insertion_device.lookup_table_models import (
    EnergyCoverage,
    LookupTable,
    LookupTableColumnConfig,
    convert_csv_to_lookup,
)
from dodal.log import LOGGER


class EnergyMotorLookup:
    """Handles a lookup table for Apple2 ID, converting energy/polarisation to a motor
    position.

    After update_lookup_table() has populated the lookup table,
    `find_value_in_lookup_table()` can be used to compute gap / phase for a requested
    energy / polarisation pair.
    """

    def __init__(self, lut: LookupTable | None = None):
        if lut is None:
            lut = LookupTable()
        self.lut = lut

    def update_lookup_table(self) -> None:
        """Do nothing by default. Sub classes may override this method to provide logic
        on what updating lookup table does.
        """
        pass

    def find_value_in_lookup_table(self, value: float, pol: Pol) -> float:
        """Convert energy and polarisation to a value from the lookup table.

        Args:
            value (float): Desired energy.
            pol (Pol): Polarisation mode.

        Returns:
            float: gap / phase motor position from the lookup table.
        """
        # if lut is empty, force an update to pull updated lut incase subclasses have
        # implemented it.
        if not self.lut.root:
            self.update_lookup_table()
        poly = self.lut.get_poly(value=value, pol=pol)
        return poly(value)


class ConfigServerEnergyMotorLookup(EnergyMotorLookup):
    """Fetches and parses lookup table (csv) from a config server, supports dynamic
    updates, and validates input.

    Args:
        config_client (ConfigServer): The config server client to fetch the look up
            table data.
        lut_config (LookupTableColumnConfig): Configuration that defines how to
            process file contents into a LookupTable.
        path (Path): File path to the lookup table.
    """

    def __init__(
        self,
        config_client: ConfigClient,
        lut_config: LookupTableColumnConfig,
        path: Path,
    ):
        self.path = path
        self.config_client = config_client
        self.lut_config = lut_config
        super().__init__()

    def read_lut(self) -> LookupTable:
        file_contents = self.config_client.get_file_contents(
            self.path, reset_cached_result=True
        )
        return convert_csv_to_lookup(file_contents, lut_config=self.lut_config)

    def update_lookup_table(self) -> None:
        self.lut = self.read_lut()


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
        poly_params: dict[Pol, list[float]] | dict[Pol, str],
        pv_start: int = 12,
        pv_end: int = 0,
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
                        start=pv_start,
                        end=pv_end,
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
