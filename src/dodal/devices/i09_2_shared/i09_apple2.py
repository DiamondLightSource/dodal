import csv
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, RootModel

ROW_PHASE_MOTOR_TOLERANCE = 0.004
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100
DEFAULT_JAW_PHASE_POLY_PARAMS = [1.0 / 7.5, -120.0 / 7.5]
ALPHA_OFFSET = 180
MAXIMUM_MOVE_TIME = 550  # There is no useful movements take longer than this.


class EnergyMinMax(BaseModel):
    Minimum: float
    Maximum: float


class EnergyCoverageEntry(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    Low: float
    High: float
    Poly: np.poly1d


class EnergyCoverage(RootModel):
    root: dict[str, EnergyCoverageEntry]


class LookupTableEntries(BaseModel):
    Energies: EnergyCoverage
    Limit: EnergyMinMax


class Lookuptable(RootModel):
    """BaseModel class for the lookup table.
    Apple2 lookup table should be in this format.

    {mode: {'Energies': {Any: {'Low': float,
                            'High': float,
                            'Poly':np.poly1d
                            }
                        }
            'Limit': {'Minimum': float,
                    'Maximum': float
                    }
        }
    }
    """

    root: dict[str, LookupTableEntries]


def convert_csv_to_lookup(
    file: str,
    source: tuple[str, str] | None,
    mode: str | None = "Mode",
    mode_name_convert: dict[str, str] | None = None,
    min_energy: str | None = "MinEnergy",
    max_energy: str | None = "MaxEnergy",
    poly_deg: list | None = None,
) -> dict[str | None, dict[str, dict[str, dict[str, Any]]]]:
    """
    Convert a CSV file to a lookup table dictionary.

    Returns
    -------
    dict
        Dictionary in Apple2 lookup table format.

    Raises
    ------
    RuntimeError
        If the CSV cannot be converted.

    """
    if mode_name_convert is None:
        mode_name_convert = {"CR": "PC", "CL": "NC"}
    if poly_deg is None:
        poly_deg = [
            "7th-order",
            "6th-order",
            "5th-order",
            "4th-order",
            "3rd-order",
            "2nd-order",
            "1st-order",
            "b",
        ]
    lookup_table = {}
    polarisations = set()

    def process_row(row: dict) -> None:
        """Process a single row from the CSV file and update the lookup table."""

        mode_value = row[mode]
        if mode_value in mode_name_convert:
            print(mode_value)
            mode_value = mode_name_convert[f"{mode_value}"]
        if mode_value not in polarisations:
            polarisations.add(mode_value)
            lookup_table[mode_value] = {
                "Energies": {},
                "Limit": {
                    "Minimum": float(row[min_energy]),
                    "Maximum": float(row[max_energy]),
                },
            }

        # Create polynomial object for energy-to-gap/phase conversion
        coefficients = [float(row[coef]) for coef in poly_deg]
        polynomial = np.poly1d(coefficients)

        lookup_table[mode_value]["Energies"][row[min_energy]] = {
            "Low": float(row[min_energy]),
            "High": float(row[max_energy]),
            "Poly": polynomial,
        }

        # Update energy limits
        lookup_table[mode_value]["Limit"]["Minimum"] = min(
            lookup_table[mode_value]["Limit"]["Minimum"], float(row[min_energy])
        )
        lookup_table[mode_value]["Limit"]["Maximum"] = max(
            lookup_table[mode_value]["Limit"]["Maximum"], float(row[max_energy])
        )

    csv_file = read_file_and_skip(file=file)
    reader = csv.DictReader(csv_file)
    # self.config_client.get_file_contents(file, reset_cached_result=True)
    # reader = csv.DictReader(io.StringIO(csv_file))

    for row in reader:
        # If there are multiple source only convert requested.
        if source is not None:
            if row[source[0]] == source[1]:
                process_row(row=row)
        else:
            process_row(row=row)

    if not lookup_table:
        raise RuntimeError(f"Unable to convert lookup table:\t{file}")
    return lookup_table


def read_file_and_skip(file: str, skip_line_start_with: str = "#"):
    with open(file) as f:
        for line in f:
            if line.startswith(skip_line_start_with):
                continue
            yield line
