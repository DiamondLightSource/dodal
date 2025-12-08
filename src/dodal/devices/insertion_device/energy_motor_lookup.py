from pathlib import Path

from daq_config_server.client import ConfigServer

from dodal.devices.insertion_device.apple2_undulator import Pol
from dodal.devices.insertion_device.lookup_table_models import (
    LookupTable,
    LookupTableColumnConfig,
    convert_csv_to_lookup,
)


class EnergyMotorLookup:
    """
    Handles a lookup table for Apple2 ID, converting energy/polarisation to a motor
    position.

    After update_lookup_table() has populated the lookup table, `find_value_in_lookup_table()`
    can be used to compute gap / phase for a requested energy / polarisation pair.
    """

    def __init__(self, lut: LookupTable | None = None):
        if lut is None:
            lut = LookupTable()
        self.lut = lut

    def update_lookup_table(self) -> None:
        """Do nothing by default. Sub classes may override this method to provide logic
        on what updating lookup table does."""
        pass

    def find_value_in_lookup_table(self, energy: float, pol: Pol) -> float:
        """
        Convert energy and polarisation to a value from the lookup table.

        Parameters:
        -----------
        energy : float
            Desired energy.
        pol : Pol
            Polarisation mode.

        Returns:
        ----------
        float
            gap / phase motor position from the lookup table.
        """
        # if lut is empty, force an update to pull updated lut incase subclasses have
        # implemented it.
        if not self.lut.root:
            self.update_lookup_table()
        poly = self.lut.get_poly(energy=energy, pol=pol)
        return poly(energy)


class ConfigServerEnergyMotorLookup(EnergyMotorLookup):
    """Fetches and parses lookup table (csv) from a config server, supports dynamic
    updates, and validates input."""

    def __init__(
        self,
        config_client: ConfigServer,
        lut_config: LookupTableColumnConfig,
        path: Path,
    ):
        """
        Parameters:
        -----------
        config_client:
            The config server client to fetch the look up table data.
        lut_config:
            Configuration that defines how to process file contents into a LookupTable
        path:
            File path to the lookup table.
        """
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
