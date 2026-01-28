"""Apple2 lookup table utilities and CSV converter.

This module provides helpers to read, validate and convert Apple2 insertion-device
lookup tables (energy -> gap/phase polynomials) from CSV sources into an
in-memory dictionary format used by the Apple2 controllers.

Data format produced
The lookup-table dictionary created by convert_csv_to_lookup() follows this
structure:

{
  "POL_MODE": {
    "energy_entries": [
        {
            "low": <float>,
            "high": <float>,
            "poly": <numpy.poly1d>
        },
      ...
    ]
  },
  ...
}
"""

import csv
import io
from collections.abc import Generator
from typing import Annotated as A
from typing import Any, NamedTuple, Self

import numpy as np
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_serializer,
    field_validator,
)

from dodal.devices.insertion_device.enum import Pol

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
ROW_PHASE_CIRCULAR = 15.0
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100

DEFAULT_POLY1D_PARAMETERS = {
    Pol.LH: [0],
    Pol.LV: [MAXIMUM_ROW_PHASE_MOTOR_POSITION],
    Pol.PC: [ROW_PHASE_CIRCULAR],
    Pol.NC: [-ROW_PHASE_CIRCULAR],
    Pol.LH3: [0],
}


class Source(NamedTuple):
    column: str
    value: str


class LookupTableColumnConfig(BaseModel):
    """Configuration on how to process a csv file columns into a LookupTable data model."""

    source: A[
        Source | None,
        Field(
            description="If not None, only process the row if the source column name match the value."
        ),
    ] = None
    mode: A[str, Field(description="Polarisation mode column name.")] = "Mode"
    min_energy: A[str, Field(description="Minimum energy column name.")] = "MinEnergy"
    max_energy: A[str, Field(description="Maximum energy column name.")] = "MaxEnergy"
    poly_deg: list[str] = Field(
        description="Polynomial column names.", default_factory=lambda: DEFAULT_POLY_DEG
    )
    mode_name_convert: dict[str, str] = Field(
        description="When processing polarisation mode values, map their alias values to a real value.",
        default_factory=lambda: MODE_NAME_CONVERT,
    )
    grating: A[
        str | None, Field(description="Optional column name for entry grating.")
    ] = None


class EnergyCoverageEntry(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True, frozen=True
    )  # arbitrary_types_allowed is True so np.poly1d can be used.
    min_energy: float
    max_energy: float
    poly: np.poly1d
    grating: float | None = None

    @field_validator("poly", mode="before")
    @classmethod
    def validate_and_convert_poly(
        cls: type[Self], value: np.poly1d | list
    ) -> np.poly1d:
        """If reading from serialized data, it will be using a list. Convert to np.poly1d"""
        if isinstance(value, list):
            return np.poly1d(value)
        return value

    @field_serializer("poly", mode="plain")
    def serialize_poly(self, value: np.poly1d) -> list:
        """Allow np.poly1d to work when serializing."""
        return value.coefficients.tolist()


class EnergyCoverage(BaseModel):
    model_config = ConfigDict(frozen=True)
    energy_entries: tuple[EnergyCoverageEntry, ...]

    @field_validator("energy_entries", mode="after")
    @classmethod
    def _prepare_energy_entries(
        cls, value: tuple[EnergyCoverageEntry, ...]
    ) -> tuple[EnergyCoverageEntry, ...]:
        """Convert incoming energy_entries to a sorted, immutable tuple."""
        return tuple(sorted(value, key=lambda e: e.min_energy))

    @classmethod
    def generate(
        cls: type[Self],
        min_energies: list[float],
        max_energies: list[float],
        poly1d_params: list[list[float]],
    ) -> Self:
        energy_entries = tuple(
            EnergyCoverageEntry(
                min_energy=min_energy,
                max_energy=max_energy,
                poly=np.poly1d(poly_params),
            )
            for min_energy, max_energy, poly_params in zip(
                min_energies, max_energies, poly1d_params, strict=True
            )
        )
        return cls(energy_entries=energy_entries)

    @property
    def min_energy(self) -> float:
        return self.energy_entries[0].min_energy

    @property
    def max_energy(self) -> float:
        return self.energy_entries[-1].max_energy

    def get_poly(self, energy: float) -> np.poly1d:
        """
        Return the numpy.poly1d polynomial applicable for the given energy.

        Parameters:
        -----------
        energy:
            Energy value in the same units used to create the lookup table.
        """

        if not self.min_energy <= energy <= self.max_energy:
            raise ValueError(
                f"Demanding energy must lie between {self.min_energy} and {self.max_energy}!"
            )

        poly_index = self.get_energy_index(energy)
        if poly_index is not None:
            return self.energy_entries[poly_index].poly
        raise ValueError(
            "Cannot find polynomial coefficients for your requested energy."
            + " There might be gap in the calibration lookup table."
        )

    def get_energy_index(self, energy: float) -> int | None:
        """Binary search assumes self.energy_entries is sorted by min_energy.
        Return index or None if not found."""
        max_index = len(self.energy_entries) - 1
        min_index = 0
        while min_index <= max_index:
            mid_index = (min_index + max_index) // 2
            en_try = self.energy_entries[mid_index]
            if en_try.min_energy <= energy <= en_try.max_energy:
                return mid_index
            elif energy < en_try.min_energy:
                max_index = mid_index - 1
            else:
                min_index = mid_index + 1
        return None


class LookupTable(RootModel[dict[Pol, EnergyCoverage]]):
    """
    Specialised lookup table for insertion devices to relate the energy and polarisation
    values to Apple2 motor positions.
    """

    model_config = ConfigDict(frozen=True)

    # Allow to auto specify a dict if one not provided
    def __init__(self, root: dict[Pol, EnergyCoverage] | None = None):
        super().__init__(root=root or {})

    @classmethod
    def generate(
        cls: type[Self],
        pols: list[Pol],
        energy_coverage: list[EnergyCoverage],
    ) -> Self:
        """Generate a LookupTable containing multiple EnergyCoverage
        for provided polarisations."""
        root_data = dict(zip(pols, energy_coverage, strict=False))
        return cls(root=root_data)

    def get_poly(
        self,
        energy: float,
        pol: Pol,
    ) -> np.poly1d:
        """
        Return the numpy.poly1d polynomial applicable for the given energy and polarisation.

        Parameters:
        -----------
        energy:
            Energy value in the same units used to create the lookup table.
        pol:
            Polarisation mode (Pol enum).
        """
        return self.root[pol].get_poly(energy)


def convert_csv_to_lookup(
    file_contents: str,
    lut_config: LookupTableColumnConfig,
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
    temp_mode_entries: dict[Pol, list[EnergyCoverageEntry]] = {}

    def process_row(row: dict[str, Any]) -> None:
        """Process a single row from the CSV file and update the temporary entry list."""
        raw_mode_value = str(row[lut_config.mode]).lower()
        mode_value = Pol(
            lut_config.mode_name_convert.get(raw_mode_value, raw_mode_value)
        )

        coefficients = np.poly1d([float(row[coef]) for coef in lut_config.poly_deg])

        energy_entry = EnergyCoverageEntry(
            min_energy=float(row[lut_config.min_energy]),
            max_energy=float(row[lut_config.max_energy]),
            poly=coefficients,
        )

        if mode_value not in temp_mode_entries:
            temp_mode_entries[mode_value] = []

        temp_mode_entries[mode_value].append(energy_entry)

    reader = csv.DictReader(read_file_and_skip(file_contents, skip_line_start_with))

    for row in reader:
        source = lut_config.source
        # If there are multiple source only convert requested.
        if source is None or row[source.column] == source.value:
            process_row(row=row)
    # Check if our LookupTable is empty after processing, raise error if it is.
    if not temp_mode_entries:
        raise RuntimeError(
            "LookupTable content is empty, failed to convert the file contents to "
            "a LookupTable!"
        )

    final_lut_root: dict[Pol, EnergyCoverage] = {}
    for pol, entries in temp_mode_entries.items():
        final_lut_root[pol] = EnergyCoverage.model_validate({"energy_entries": entries})

    return LookupTable(root=final_lut_root)


def read_file_and_skip(file: str, skip_line_start_with: str = "#") -> Generator[str]:
    """Yield non-comment lines from the CSV content string."""
    for line in io.StringIO(file):
        if line.startswith(skip_line_start_with):
            continue
        else:
            yield line
