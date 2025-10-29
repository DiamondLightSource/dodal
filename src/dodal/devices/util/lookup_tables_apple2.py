"""Apple2 lookuptable definition and csv converter"""

import abc
import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from daq_config_server.client import ConfigServer
from pydantic import BaseModel, ConfigDict, RootModel

from dodal.devices.apple2_undulator import Pol


@dataclass
class LookupPath:
    Gap: Path | None
    Phase: Path | None


@dataclass
class LookupTableConfig:
    path: LookupPath
    source: tuple[str, str] | None
    mode: str | None
    min_energy: str | None
    max_energy: str | None
    poly_deg: list | None


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
    source: tuple[str, str] | None = None,
    mode: str | None = "Mode",
    mode_name_convert: dict[str, str] | None = None,
    min_energy: str | None = "MinEnergy",
    max_energy: str | None = "MaxEnergy",
    poly_deg: list | None = None,
    skip_line_start_with: str = "#",
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

    reader = csv.DictReader(read_file_and_skip(file, skip_line_start_with))

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
    for line in io.StringIO(file):
        if line.startswith(skip_line_start_with):
            continue
        else:
            yield line


def get_poly(
    energy: float,
    pol: Pol,
    lookup_table: dict[str | None, dict[str, dict[str, Any]]],
) -> np.poly1d:
    """
    Get polynomial for a given energy and polarisation.

    Raises
    ------
    ValueError
        If energy is out of bounds or coefficients are missing.
    """
    if (
        energy < lookup_table[pol]["Limit"]["Minimum"]
        or energy > lookup_table[pol]["Limit"]["Maximum"]
    ):
        raise ValueError(
            "Demanding energy must lie between {} and {} eV!".format(
                lookup_table[pol]["Limit"]["Minimum"],
                lookup_table[pol]["Limit"]["Maximum"],
            )
        )
    else:
        for energy_range in lookup_table[pol]["Energies"].values():
            if energy >= energy_range["Low"] and energy < energy_range["High"]:
                return energy_range["Poly"]

    raise ValueError(
        "Cannot find polynomial coefficients for your requested energy."
        + " There might be gap in the calibration lookup table."
    )


def generate_lookup_table(
    pol: Pol, min_energy: float, max_energy: float, poly1d_param: list[float]
) -> dict[str | None, dict[str, dict[str, Any]]]:
    return {
        pol.value: {
            "Energies": {
                f"{min_energy}": {
                    "Low": min_energy,
                    "High": max_energy,
                    "Poly": np.poly1d(poly1d_param),
                },
            },
            "Limit": {"Minimum": min_energy, "Maximum": max_energy},
        }
    }


def make_phase_tables(
    pols: list[Pol],
    min_energies: list[float],
    max_energies: list[float],
    poly1d_params: list[list[float]],
) -> dict[str | None, dict[str, dict[str, Any]]]:
    lookuptable_phase = {}
    for i in range(len(pols)):
        lookuptable_phase.update(
            generate_lookup_table(
                pol=pols[i],
                min_energy=min_energies[i],
                max_energy=max_energies[i],
                poly1d_param=poly1d_params[i],
            )
        )
    return lookuptable_phase


class EnergyMotorLookup:
    """
    Handles lookup tables for I10 Apple2 ID, converting energy and polarisation to gap
     and phase. Fetches and parses lookup tables from a config server, supports dynamic
     updates, and validates input.
    """

    def __init__(
        self,
        lookuptable_dir: str,
        config_client: ConfigServer,
        source: tuple[str, str] | None = None,
        mode: str = "Mode",
        min_energy: str = "MinEnergy",
        max_energy: str = "MaxEnergy",
        gap_file_name: str = "IDEnergy2GapCalibrations.csv",
        phase_file_name: str | None = "IDEnergy2PhaseCalibrations.csv",
        poly_deg: list | None = None,
    ):
        """Initialise the I10EnergyMotorLookup class with lookup table headers provided.

        Parameters
        ----------
        look_up_table_dir:
            The path to look up table.
        source:
            The column name and the name of the source in look up table. e.g. ( "source", "idu")
        config_client:
            The config server client to fetch the look up table.
        mode:
            The column name of the mode in look up table.
        min_energy:
            The column name that contain the maximum energy in look up table.
        max_energy:
            The column name that contain the maximum energy in look up table.
        poly_deg:
            The column names for the parameters for the energy conversion polynomial, starting with the least significant.

        """
        self.lookup_tables: dict[str, dict[str | None, dict[str, dict[str, Any]]]] = {
            "Gap": {},
            "Phase": {},
        }
        energy_gap_table_path = Path(lookuptable_dir, gap_file_name)
        if phase_file_name is not None:
            energy_phase_table_path = Path(lookuptable_dir, phase_file_name)
        else:
            energy_phase_table_path = None
        self.lookup_table_config = LookupTableConfig(
            path=LookupPath(energy_gap_table_path, energy_phase_table_path),
            mode=mode,
            source=source,
            min_energy=min_energy,
            max_energy=max_energy,
            poly_deg=poly_deg,
        )
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
        ...

    def get_motor_from_energy(self, energy: float, pol: Pol) -> tuple[float, float]:
        """
        Convert energy and polarisation to gap and phase motor positions.

        Parameters
        ----------
        energy : float
            Desired energy in eV.
        pol : Pol
            Polarisation mode.

        Returns
        -------
        tuple[float, float]
            (gap, phase) motor positions.

        """
        if self.available_pol == []:
            self.update_lookuptable()

        gap_poly = get_poly(
            lookup_table=self.lookup_tables["Gap"], energy=energy, pol=pol
        )
        phase_poly = get_poly(
            lookup_table=self.lookup_tables["Phase"], energy=energy, pol=pol
        )
        return gap_poly(energy), phase_poly(energy)
