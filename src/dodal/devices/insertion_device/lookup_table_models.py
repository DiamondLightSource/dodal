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
from typing import Self

import numpy as np
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_serializer,
    field_validator,
)

from dodal.devices.insertion_device.apple2_undulator import Pol

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

DEFAULT_POLY1D_PARAMETERS = {
    Pol.LH: [0],
    Pol.LV: [MAXIMUM_ROW_PHASE_MOTOR_POSITION],
    Pol.PC: [ROW_PHASE_CIRCULAR],
    Pol.NC: [-ROW_PHASE_CIRCULAR],
    Pol.LH3: [0],
}


class LookupTableConfig(BaseModel):
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


class LookupTableEntry(BaseModel):
    energies: EnergyCoverage
    limit: EnergyMinMax

    @classmethod
    def generate(
        cls: type[Self], min_energy: float, max_energy: float, poly1d_param: list[float]
    ) -> Self:
        return cls(
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


class LookupTable(RootModel[dict[Pol, LookupTableEntry]]):
    # Allow to auto specify a dict if one not provided
    def __init__(self, root: dict[Pol, LookupTableEntry] | None = None):
        super().__init__(root=root or {})

    @classmethod
    def generate(
        cls: type[Self],
        pols: list[Pol],
        min_energies: list[float],
        max_energies: list[float],
        poly1d_params: list[list[float]],
    ) -> Self:
        """Generate a dictionary containing multiple lookuptable entries
        for provided polarisations."""
        lut = cls()
        for i in range(len(pols)):
            lut.root[pols[i]] = LookupTableEntry.generate(
                min_energy=min_energies[i],
                max_energy=max_energies[i],
                poly1d_param=poly1d_params[i],
            )
        return lut

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
        if (
            energy < self.root[pol].limit.minimum
            or energy > self.root[pol].limit.maximum
        ):
            raise ValueError(
                "Demanding energy must lie between"
                + f" {self.root[pol].limit.minimum}"
                + f" and {self.root[pol].limit.maximum} eV!"
            )
        else:
            for energy_range in self.root[pol].energies.root.values():
                if energy >= energy_range.low and energy < energy_range.high:
                    return energy_range.poly

        raise ValueError(
            "Cannot find polynomial coefficients for your requested energy."
            + " There might be gap in the calibration lookup table."
        )


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

    def process_row(row: dict, lut: LookupTable) -> None:
        """Process a single row from the CSV file and update the lookup table."""
        mode_value = str(row[lut_config.mode]).lower()
        if mode_value in lut_config.mode_name_convert:
            mode_value = lut_config.mode_name_convert[f"{mode_value}"]
        mode_value = Pol(mode_value)

        # Create polynomial object for energy-to-gap/phase conversion
        coefficients = [float(row[coef]) for coef in lut_config.poly_deg]
        if mode_value not in lut.root:
            lut.root[mode_value] = LookupTableEntry.generate(
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
