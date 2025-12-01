from pathlib import Path

import numpy as np
from daq_config_server.client import ConfigServer

from dodal.devices.insertion_device.apple2_undulator import Pol
from dodal.devices.insertion_device.lookup_table_models import (
    LookupTable,
    LookupTableConfig,
    convert_csv_to_lookup,
)


def get_poly(
    energy: float,
    pol: Pol,
    lookup_table: LookupTable,
) -> np.poly1d:
    """
    Return the numpy.poly1d polynomial applicable for the given energy and polarisation.

    Parameters:
    -----------
    energy:
        Energy value in the same units used to create the lookup table.
    pol:
        Polarisation mode (Pol enum).
    lookup_table:
        The converted lookup table dictionary for either 'gap' or 'phase'.
    """
    if (
        energy < lookup_table.root[pol].limit.minimum
        or energy > lookup_table.root[pol].limit.maximum
    ):
        raise ValueError(
            "Demanding energy must lie between"
            + f" {lookup_table.root[pol].limit.minimum}"
            + f" and {lookup_table.root[pol].limit.maximum} eV!"
        )
    else:
        for energy_range in lookup_table.root[pol].energies.root.values():
            if energy >= energy_range.low and energy < energy_range.high:
                return energy_range.poly

    raise ValueError(
        "Cannot find polynomial coefficients for your requested energy."
        + " There might be gap in the calibration lookup table."
    )


class EnergyMotorLookup:
    """
    Handles a lookup table for Apple2 ID, converting energy/polarisation to a motor
    position.

    After update_lookup_table() has populated the lookup table, `find_value_in_lookup_table()` can be
    used to compute gap / phase for a requested energy / polarisation pair.
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
        # if lut is empty, force an update to pull updated file.
        if not self.lut.root:
            self.update_lookup_table()
        poly = get_poly(lookup_table=self.lut, energy=energy, pol=pol)
        return poly(energy)


class ConfigServerEnergyMotorLookup(EnergyMotorLookup):
    """Fetches and parses lookup table (csv) from a config server, supports dynamic
    updates, and validates input."""

    def __init__(
        self,
        config_client: ConfigServer,
        lut_config: LookupTableConfig,
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
