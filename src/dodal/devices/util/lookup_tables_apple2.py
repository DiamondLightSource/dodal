"""Apple2 lookup table utilities and CSV converter.

This module provides helpers to read, validate and convert Apple2 insertion-device
lookup tables (energy -> gap/phase polynomials) from CSV sources into an
in-memory dictionary format used by the Apple2 controllers.

Data format produced
The lookup-table dictionary created by convert_csv_to_lookup() follows this
structure:

{
  "POL_MODE": {
    "energies": {
      "<min_energy>": {
        "low": <float>,
        "high": <float>,
        "poly": <numpy.poly1d>
      },
      ...
    },
    "limit": {
      "minimum": <float>,
      "maximum": <float>
    }
  },
}

"""

import csv
import io
from collections.abc import Generator
from pathlib import Path

import numpy as np
from daq_config_server.client import ConfigServer
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_serializer,
    field_validator,
)

from dodal.devices.apple2_undulator import Pol
from dodal.log import LOGGER


def default_gap_file(path: str, file: str = "IDEnergy2GapCalibrations.csv") -> Path:
    return Path(path, file)


def default_phase_file(path: str, file: str = "IDEnergy2PhaseCalibrations.csv") -> Path:
    return Path(path, file)


DEFAULT_POLY_DEG = [
    "7th-order",
    "6th-order",
    "5th-order",
    "4th-order",
    "3rd-order",
    "2nd-order",
    "1st-order",
    "b",
]

MODE_NAME_CONVERT = {"CR": "pc", "CL": "nc"}


class LookupTableConfig(BaseModel):
    path: Path
    source: tuple[str, str] | None = None
    mode: str = "Mode"
    min_energy: str = "MinEnergy"
    max_energy: str = "MaxEnergy"
    poly_deg: list[str] = Field(default_factory=lambda: DEFAULT_POLY_DEG)
    mode_name_convert: dict[str, str] = Field(default_factory=lambda: MODE_NAME_CONVERT)


class EnergyMinMax(BaseModel):
    minimum: float
    maximum: float


class EnergyCoverageEntry(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)  # So np.poly1d can be used.
    low: float
    high: float
    poly: np.poly1d

    @field_validator("poly", mode="before")
    @classmethod
    def validate_and_convert_poly(cls, value):
        """If reading from serialized data, it will be using a list. Convert to np.poly1d"""
        if isinstance(value, list):
            return np.poly1d(value)
        return value

    @field_serializer("poly", mode="plain")
    def serialize_poly(self, value: np.poly1d) -> list:
        """Allow np.poly1d to work when serializing."""
        return value.coefficients.tolist()


class EnergyCoverage(RootModel[dict[float, EnergyCoverageEntry]]):
    pass


class LookupTableEntries(BaseModel):
    energies: EnergyCoverage
    limit: EnergyMinMax


class LookupTable(RootModel[dict[Pol, LookupTableEntries]]):
    # Allow to auto specify a dict if one not provided
    def __init__(self, root: dict[Pol, LookupTableEntries] | None = None):
        super().__init__(root=root or {})


class GapPhaseLookupTables(BaseModel):
    gap: LookupTable = Field(default_factory=lambda: LookupTable())
    gap_config: LookupTableConfig

    phase: LookupTable = Field(default_factory=lambda: LookupTable())
    phase_config: LookupTableConfig


def convert_csv_to_lookup(
    config_client: ConfigServer,
    lut_config: LookupTableConfig,
    skip_line_start_with: str = "#",
) -> LookupTable:
    """
    Convert CSV content into the Apple2 lookup-table dictionary.

    Parameters:
    -----------
    config_client:
        The client that is able to retrieve the file contents.
    lut_config:
        The configuration that defines which file to read for the config_client and how
        to process the file contents into a LookupTable.
    skip_line_start_with
        Lines beginning with this prefix are skipped (default "#").

    Returns:
    -----------
    LookupTable
    """

    def process_row(row: dict, lut: LookupTable):
        """Process a single row from the CSV file and update the lookup table."""
        mode_value = str(row[lut_config.mode]).lower()
        if mode_value in lut_config.mode_name_convert:
            mode_value = lut_config.mode_name_convert[f"{mode_value}"]
        mode_value = Pol(mode_value)

        # Create polynomial object for energy-to-gap/phase conversion
        coefficients = [float(row[coef]) for coef in lut_config.poly_deg]
        if mode_value not in lut.root:
            lut.root[mode_value] = generate_lookup_table_entry(
                min_energy=float(row[lut_config.min_energy]),
                max_energy=float(row[lut_config.max_energy]),
                poly1d_param=coefficients,
            )

        else:
            lut.root[mode_value].energies.root[float(row[lut_config.min_energy])] = (
                EnergyCoverageEntry(
                    low=float(row[lut_config.min_energy]),
                    high=float(row[lut_config.max_energy]),
                    poly=np.poly1d(coefficients),
                )
            )

        # Update energy limits
        lut.root[mode_value].limit.minimum = min(
            lut.root[mode_value].limit.minimum,
            float(row[lut_config.min_energy]),
        )
        lut.root[mode_value].limit.maximum = max(
            lut.root[mode_value].limit.maximum,
            float(row[lut_config.max_energy]),
        )
        return lut

    file_contents = config_client.get_file_contents(
        lut_config.path, reset_cached_result=True
    )
    reader = csv.DictReader(read_file_and_skip(file_contents, skip_line_start_with))
    lut = LookupTable()

    for row in reader:
        # If there are multiple source only convert requested.
        if lut_config.source is not None:
            if row[lut_config.source[0]] == lut_config.source[1]:
                process_row(row=row, lut=lut)
        else:
            process_row(row=row, lut=lut)

    # Check if our LookupTable is empty after processing, raise error if it is.
    if not lut.root:
        raise RuntimeError(
            "LookupTable content is empty, failed to convert the file contents to "
            "a LookupTable!"
        )
    return lut


def read_file_and_skip(file: str, skip_line_start_with: str = "#") -> Generator[str]:
    """Yield non-comment lines from the CSV content string."""
    for line in io.StringIO(file):
        if line.startswith(skip_line_start_with):
            continue
        else:
            yield line


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
        Energy value in the same units used to create the lookup table (eV).
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


def generate_lookup_table_entry(
    min_energy: float, max_energy: float, poly1d_param: list[float]
) -> LookupTableEntries:
    return LookupTableEntries(
        energies=EnergyCoverage(
            {
                min_energy: EnergyCoverageEntry(
                    low=min_energy,
                    high=max_energy,
                    poly=np.poly1d(poly1d_param),
                )
            }
        ),
        limit=EnergyMinMax(
            minimum=float(min_energy),
            maximum=float(max_energy),
        ),
    )


def generate_lookup_table(
    pol: Pol, min_energy: float, max_energy: float, poly1d_param: list[float]
) -> LookupTable:
    return LookupTable(
        {pol: generate_lookup_table_entry(min_energy, max_energy, poly1d_param)}
    )


def make_phase_tables(
    pols: list[Pol],
    min_energies: list[float],
    max_energies: list[float],
    poly1d_params: list[list[float]],
) -> LookupTable:
    """Generate a dictionary containing multiple lookuptable entries
    for provided polarisations."""
    lookuptable_phase = LookupTable()
    for i in range(len(pols)):
        lookuptable_phase.root[pols[i]] = generate_lookup_table_entry(
            min_energy=min_energies[i],
            max_energy=max_energies[i],
            poly1d_param=poly1d_params[i],
        )

    return lookuptable_phase


class EnergyMotorLookup:
    """
    Handles lookup tables for Apple2 ID, converting energy and polarisation to gap
    and phase. Fetches and parses lookup tables from a config server, supports dynamic
    updates, and validates input. If custom logic is required for lookup tables, sub
    classes should override the _update_gap_lut and _update_phase_lut methods.

    After update_lookuptable() has populated the 'gap' and 'phase' tables,
    `get_motor_from_energy()` can be used to compute (gap, phase) for a requested
    (energy, pol) pair.
    """

    def __init__(
        self,
        config_client: ConfigServer,
        gap_lut_config: LookupTableConfig,
        phase_lut_config: LookupTableConfig,
    ):
        """Initialise the EnergyMotorLookup class with lookup table headers provided.

        Parameters:
        -----------
        lut_config:
            The configuration that contains the lookup table file paths and how to read
            them.
        config_client:
            The config server client to fetch the look up table.
        """
        self.lookup_tables = GapPhaseLookupTables(
            gap_config=gap_lut_config, phase_config=phase_lut_config
        )
        self.config_client = config_client
        self._available_pol = []

    @property
    def available_pol(self) -> list[Pol]:
        return self._available_pol

    @available_pol.setter
    def available_pol(self, value: list[Pol]) -> None:
        self._available_pol = value

    def _update_gap_lut(self) -> None:
        self.lookup_tables.gap = convert_csv_to_lookup(
            config_client=self.config_client, lut_config=self.lookup_tables.gap_config
        )
        self.available_pol = list(self.lookup_tables.gap.root.keys())

    def _update_phase_lut(self) -> None:
        self.lookup_tables.phase = convert_csv_to_lookup(
            config_client=self.config_client, lut_config=self.lookup_tables.phase_config
        )

    def update_lookuptables(self):
        """
        Update lookup tables from files and validate their format.
        """
        LOGGER.info("Updating lookup dictionary from file for gap.")
        self._update_gap_lut()
        LOGGER.info("Updating lookup dictionary from file for phase.")
        self._update_phase_lut()

    def get_motor_from_energy(self, energy: float, pol: Pol) -> tuple[float, float]:
        """
        Convert energy and polarisation to gap and phase motor positions.

        Parameters:
        -----------
        energy : float
            Desired energy in eV.
        pol : Pol
            Polarisation mode.

        Returns:
        ----------
        tuple[float, float]
            (gap, phase) motor positions.
        """
        if self.available_pol == []:
            self.update_lookuptables()

        gap_poly = get_poly(lookup_table=self.lookup_tables.gap, energy=energy, pol=pol)
        phase_poly = get_poly(
            lookup_table=self.lookup_tables.phase,
            energy=energy,
            pol=pol,
        )
        return gap_poly(energy), phase_poly(energy)
