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


class StaticPolynomialEnergyMotorLookup(EnergyMotorLookup):
    """A lookup table where polynomial coefficients are fixed at initialization.

    This class serves as the base for polynomial-based energy/motor conversions.
    It generates an internal LookupTable by evaluating a dictionary of
    polarization-specific coefficient lists across a defined value range.

    Args:
        max_value (float): The maximum valid input value (e.g., Energy in eV).
        min_value (float): The minimum valid input value.
        poly_params (dict[Pol, list[float]]): Mapping of Polarization to a
            list of polynomial coefficients (ordered by power).
    """

    def __init__(
        self,
        max_value: float,
        min_value: float,
        poly_params: dict[Pol, list[float]],
    ) -> None:
        self.min_value = min_value
        self.max_value = max_value
        self.poly_params = poly_params

        # Initialize with the static data immediately
        entries = self._generate_entries(self.poly_params)
        super().__init__(LookupTable(entries))

    def _generate_entries(
        self, param_dict: dict[Pol, list[float]]
    ) -> dict[Pol, EnergyCoverage]:
        return {
            pol: EnergyCoverage.generate(
                min_energies=[self.min_value],
                max_energies=[self.max_value],
                poly1d_params=[coeffs],
            )
            for pol, coeffs in param_dict.items()
        }


class EpicsPolynomialEnergyMotorLookup(
    Device, Triggerable, StaticPolynomialEnergyMotorLookup
):
    """A specialized lookup device that synchronizes polynomial coefficients
    directly from EPICS PVs.

    This device extends the static lookup by introducing Ophyd-async signals
    (DeviceVectors) to fetch live calibration data from an IOC. It allows
    physics tables to be updated dynamically without restarting the control
    system or manually reloading CSV files.

    It implements the `Triggerable` protocol to allow on-demand table
    regeneration within a Bluesky plan.

    Args:
        prefix (str): The EPICS prefix for the polynomial coefficient PVs.
        max_value (float): The maximum valid input value for the lookup.
        min_value (float): The minimum valid input value for the lookup.
        poly_params (dict[Pol, str]): Mapping of Polarization to the PV
            suffix (e.g., {Pol.LH: "HZ"}).
        pv_start (int, optional): The starting index of the PV coefficient
            (e.g., 12 for C12). Defaults to 12.
        pv_end (int, optional): The ending index of the PV coefficient
            (e.g., 1 for C1). Defaults to 1.
        name (str, optional): Name of the device for logging and Bluesky.

    Attributes:
        param_dict (dict[Pol, DeviceVector]): Dictionary of signals used to
            fetch coefficients for each polarization.
    """

    def __init__(
        self,
        prefix: str,
        max_value: float,
        min_value: float,
        poly_params: dict[Pol, str],
        pv_start: int = 12,
        pv_end: int = 1,
        name: str = "",
    ) -> None:
        self.param_dict = {}
        self.min_value = min_value
        self.max_value = max_value
        for pol, suffix in poly_params.items():
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
        super().__init__(name=name)

    def _make_params(self, pv_prefix: str, start: int, end: int) -> DeviceVector:
        sign = 1 if start < end else -1
        return DeviceVector(
            {
                i: epics_signal_rw(float, read_pv=f"{pv_prefix}:C{i}")
                for i in range(start, end + sign, sign)
            }
        )

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        """Triggering this device will update the lookup tables with the current PV values."""
        await self.update_lookup()

    async def update_lookup(self) -> None:
        """Fetch the latest polynomial coefficients from EPICS, update the lookup table,
        and handle any errors that occur during the process.
        """
        try:
            pols = list(self.param_dict.keys())
            vectors = list(self.param_dict.values())
            poly_values = await asyncio.gather(
                *(asyncio.gather(*(p.get_value() for p in v.values())) for v in vectors)
            )
            current_coeffs = {
                pol: list(val) for pol, val in zip(pols, poly_values, strict=True)
            }

            self.lut = LookupTable(self._generate_entries(current_coeffs))
            LOGGER.info(f"Successfully synced {self.name} from EPICS.")
        except Exception as e:
            LOGGER.error(f"Failed to update {self.name}: {e}")
            raise

    def update_lookup_table(self) -> None:
        """Overrides the base synchronous method to provide a warning.
        Since EPICS communication is asynchronous, use 'await update_lookup()' instead.
        """
        LOGGER.warning(
            f"Synchronous update_lookup_table called on {self.name}. "
            "This does nothing for EPICS-based lookups. "
            "Please use 'await device.update_lookup()' or 'yield from bps.trigger(device)'."
        )

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
