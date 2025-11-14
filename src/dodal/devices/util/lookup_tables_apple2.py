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

import abc
import csv
import io
from collections.abc import Generator
from pathlib import Path
from typing import Any

import numpy as np
from daq_config_server.client import ConfigServer
from pydantic import BaseModel, ConfigDict, Field, RootModel

from dodal.devices.apple2_undulator import Pol


class LookupPath(BaseModel):
    gap: Path
    phase: Path

    @classmethod
    def create(
        cls,
        path: str,
        gap_file: str = "IDEnergy2GapCalibrations.csv",
        phase_file: str = "IDEnergy2GapCalibrations.csv",
    ) -> "LookupPath":
        """
        Factory method to easily create LookupPath using some default file names.
        Args:
            path:
                The file path to the lookup tables.
            gap_file:
                The gap lookup table file name.
            phase_file:
                The phase lookup table file name.

        Returns:
            LookupPath instance.
        """
        return cls(gap=Path(path, gap_file), phase=Path(path, phase_file))


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


class LookupTableColumnConfig(BaseModel):
    path: LookupPath
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
    model_config = ConfigDict(arbitrary_types_allowed=True)
    low: float
    high: float
    poly: np.poly1d


class EnergyCoverage(RootModel[dict[str, EnergyCoverageEntry]]):
    pass


class LookupTableEntries(BaseModel):
    energies: EnergyCoverage
    limit: EnergyMinMax


class LookupTable(RootModel[dict[str, LookupTableEntries]]):
    # Allow to auto speficy a dict if one not provided
    def __init__(self, root: dict[str, LookupTableEntries] | None = None):
        super().__init__(root=root or {})


class GapPhaseLookupTable(BaseModel):
    gap: LookupTable = Field(default_factory=lambda: LookupTable())
    phase: LookupTable = Field(default_factory=lambda: LookupTable())


def convert_csv_to_lookup(
    file_contents: str,
    lut_column_config: LookupTableColumnConfig,
    skip_line_start_with: str = "#",
) -> LookupTable:
    """
    Convert CSV content into the Apple2 lookup-table dictionary.

    args:
        file_contents:
            The CSV file content as a string.
        lut_column_config:
            The configuration that defines how to read the file_contents into a LookupTable
        skip_line_start_with
            Lines beginning with this prefix are skipped (default "#").
    """

    def process_row(row: dict[str, Any], lut: LookupTable):
        """Process a single row from the CSV file and update the lookup table."""
        mode_value = str(row[lut_column_config.mode]).lower()
        if mode_value in lut_column_config.mode_name_convert:
            mode_value = lut_column_config.mode_name_convert[f"{mode_value}"]

        # Create polynomial object for energy-to-gap/phase conversion
        coefficients = [float(row[coef]) for coef in lut_column_config.poly_deg]
        if mode_value not in lut.root:
            lut.root[Pol(mode_value)] = generate_lookup_table_entry(
                min_energy=float(row[lut_column_config.min_energy]),
                max_energy=float(row[lut_column_config.max_energy]),
                poly1d_param=coefficients,
            )

        else:
            lut.root[mode_value].energies.root[row[lut_column_config.min_energy]] = (
                EnergyCoverageEntry(
                    low=float(row[lut_column_config.min_energy]),
                    high=float(row[lut_column_config.max_energy]),
                    poly=np.poly1d(coefficients),
                )
            )

        # Update energy limits
        lut.root[mode_value].limit.minimum = min(
            lut.root[mode_value].limit.minimum,
            float(row[lut_column_config.min_energy]),
        )
        lut.root[mode_value].limit.maximum = max(
            lut.root[mode_value].limit.maximum,
            float(row[lut_column_config.max_energy]),
        )
        return lut

    reader = csv.DictReader(read_file_and_skip(file_contents, skip_line_start_with))
    lut = LookupTable()

    for row in reader:
        # If there are multiple source only convert requested.
        if lut_column_config.source is not None:
            if row[lut_column_config.source[0]] == lut_column_config.source[1]:
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

    Args:
        energy:
            Energy value in the same units used to create the lookup table (eV).
        pol:
            Polarisation mode (Pol enum).
        lookup_table:
            The converted lookup-table dictionary for either 'gap' or 'phase'.
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
                str(min_energy): EnergyCoverageEntry(
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


class BaseEnergyMotorLookup:
    """
    Abstract base for energy->motor lookup.

    Subclasses should implement `update_lookuptable()` to populate `self.lookup_tables`
    from the configured file sources. After update_lookuptable() has populated the
    'gap' and 'phase' tables, `get_motor_from_energy()` can be used to compute
    (gap, phase) for a requested (energy, pol) pair.
    """

    def __init__(
        self,
        config_client: ConfigServer,
        lut_column_config: LookupTableColumnConfig,
    ):
        """Initialise the EnergyMotorLookup class with lookup table headers provided.

        Args:
            lut_column_config:
                The configuration that contains the lookup table file paths and how to
                read them.
            config_client:
                The config server client to fetch the look up table.
        """
        self.lookup_tables = GapPhaseLookupTable()
        self.lut_column_config = lut_column_config
        self.config_client = config_client
        self._available_pol = []

    @property
    def available_pol(self) -> list[str | None]:
        return self._available_pol

    @available_pol.setter
    def available_pol(self, value: list[str | None]) -> None:
        self._available_pol = value

    @abc.abstractmethod
    def update_lookuptable(self):
        """
        Update lookup tables from files and validate their format.
        """

    def get_motor_from_energy(self, energy: float, pol: Pol) -> tuple[float, float]:
        """
        Convert energy and polarisation to gap and phase motor positions.

        Args:
            energy : float
                Desired energy in eV.
            pol : Pol
                Polarisation mode.

        Returns:
            tuple[float, float]
                (gap, phase) motor positions.

        """
        if self.available_pol == []:
            self.update_lookuptable()

        gap_poly = get_poly(lookup_table=self.lookup_tables.gap, energy=energy, pol=pol)
        phase_poly = get_poly(
            lookup_table=self.lookup_tables.phase,
            energy=energy,
            pol=pol,
        )
        return gap_poly(energy), phase_poly(energy)
