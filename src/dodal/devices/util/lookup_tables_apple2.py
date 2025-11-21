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

MODE_NAME_CONVERT = {"cr": "pc", "cl": "nc"}
DEFAULT_GAP_FILE = "IDEnergy2GapCalibrations.csv"
DEFAULT_PHASE_FILE = "IDEnergy2PhaseCalibrations.csv"

ROW_PHASE_MOTOR_TOLERANCE = 0.004
ROW_PHASE_CIRCULAR = 15
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100

PhasePoly1dParameters = {
    "lh": [0],
    "lv": [MAXIMUM_ROW_PHASE_MOTOR_POSITION],
    "pc": [ROW_PHASE_CIRCULAR],
    "nc": [-ROW_PHASE_CIRCULAR],
    "lh3": [0],
}


class LookupTableConfig(BaseModel):
    source: tuple[str, str] | None = None
    mode: str = "Mode"
    min_energy: str = "MinEnergy"
    max_energy: str = "MaxEnergy"
    grading: str | None = None
    poly_deg: list[str] = Field(default_factory=lambda: DEFAULT_POLY_DEG)
    mode_name_convert: dict[str, str] = Field(default_factory=lambda: MODE_NAME_CONVERT)
    gap_path: Path | None = None
    phase_path: Path | None = None


class EnergyMinMax(BaseModel):
    minimum: float
    maximum: float


class EnergyCoverageEntry(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)  # So np.poly1d can be used.
    low: float
    high: float
    poly: np.poly1d
    grading: str | None = None

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
    phase: LookupTable = Field(default_factory=lambda: LookupTable())


def convert_csv_to_lookup(
    file_contents: str,
    lut_config: LookupTableConfig,
    skip_line_start_with: str = "#",
) -> LookupTable:
    """
    Convert CSV content into the Apple2 lookup-table dictionary.

    Parameters:
    -----------
    file_contents:
        The CSV file contents as string.
    lut_config:
        The configuration that how to process the file_contents into a LookupTable.
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
        mode_value = Pol(mode_value.replace(" ", ""))

        # Create polynomial object for energy-to-gap/phase conversion
        coefficients = [float(row[coef]) for coef in lut_config.poly_deg]
        grading = row[lut_config.grading] if lut_config.grading else None
        if mode_value not in lut.root:
            lut.root[mode_value] = generate_lookup_table_entry(
                min_energy=float(row[lut_config.min_energy]),
                max_energy=float(row[lut_config.max_energy]),
                poly1d_param=coefficients,
                grading=grading,
            )

        else:
            lut.root[mode_value].energies.root[float(row[lut_config.min_energy])] = (
                EnergyCoverageEntry(
                    low=float(row[lut_config.min_energy]),
                    high=float(row[lut_config.max_energy]),
                    poly=np.poly1d(coefficients),
                    grading=grading,
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


def generate_lookup_table_entry(
    min_energy: float,
    max_energy: float,
    poly1d_param: list[float],
    grading: str | None = None,
) -> LookupTableEntries:
    return LookupTableEntries(
        energies=EnergyCoverage(
            {
                min_energy: EnergyCoverageEntry(
                    low=min_energy,
                    high=max_energy,
                    poly=np.poly1d(poly1d_param),
                    grading=grading,
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
        lut_config: LookupTableConfig,
    ):
        """Initialise the EnergyMotorLookup class with lookup table headers provided.

        Parameters:
        -----------
        config_client:
            The config server client to fetch the look up table data.
        lut_config:
            Configuration that defines how to process file contents into a LookupTable
        gap_path:
            File path to the gap lookup table.
        phase_path:
            File path to the phase lookup table.
        """
        self.lookup_tables = GapPhaseLookupTables()
        self.config_client = config_client
        self.lut_config = lut_config
        self._available_pol = []

    @property
    def available_pol(self) -> list[Pol]:
        return self._available_pol

    @available_pol.setter
    def available_pol(self, value: list[Pol]) -> None:
        self._available_pol = value

    def _update_gap_lut(self) -> None:
        if self.lut_config.gap_path is None:
            raise RuntimeError("Gap path is not provided!")
        file_contents = self.config_client.get_file_contents(
            self.lut_config.gap_path, reset_cached_result=True
        )
        self.lookup_tables.gap = convert_csv_to_lookup(
            file_contents, lut_config=self.lut_config
        )
        self.available_pol = list(self.lookup_tables.gap.root.keys())

    def _update_phase_lut(self) -> None:
        if self.lut_config.phase_path is None:
            raise RuntimeError("Phase path is not provided!")
        file_contents = self.config_client.get_file_contents(
            self.lut_config.phase_path, reset_cached_result=True
        )
        self.lookup_tables.phase = convert_csv_to_lookup(
            file_contents, lut_config=self.lut_config
        )

    def update_lookuptables(self):
        """
        Update lookup tables from files and validate their format.
        """
        LOGGER.info("Updating lookup table for gap.")
        self._update_gap_lut()
        if self.lut_config.phase_path is None:
            LOGGER.info("Generating lookup table for phase.")
            self._generate_phase_lut()

        else:
            LOGGER.info("Updating lookup table for phase.")
            self._update_phase_lut()

    def _generate_phase_lut(self):
        for key in self.lookup_tables.gap.root.keys():
            if key is not None:
                self.lookup_tables.phase.root[Pol(key.lower())] = (
                    generate_lookup_table_entry(
                        min_energy=self.lookup_tables.gap.root[
                            Pol(key.lower())
                        ].limit.minimum,
                        max_energy=self.lookup_tables.gap.root[
                            Pol(key.lower())
                        ].limit.maximum,
                        poly1d_param=(PhasePoly1dParameters[Pol(key.lower())]),
                    )
                )

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
