import asyncio
import csv
from pathlib import Path
from typing import Any

import numpy as np
from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    HintedSignal,
    StandardReadable,
    soft_signal_rw,
)

from dodal.devices.apple2_undulator import (
    Apple2,
    Apple2Val,
    Lookuptable,
    UndlatorPhaseAxes,
    UndulatorGap,
)
from dodal.devices.pgm import PGM
from dodal.log import LOGGER

ROW_PHASE_MOTOR_TOLERANCE = 0.004
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100


class I10Apple2(Apple2):
    """
    I10Apple2 is the i10 version of Apple2 ID.
    The set and update_lookuptable should be the only part that is I10 specific.

    A pair of look up tables are needed to provide the conversion
     between motor position and energy.
    Set is in energy(eV).

    Parameters
    ----------
    id_gap:
        An UndulatorGap device.
    id_phase:
        An UndlatorPhaseAxes device.
    energy_gap_table_path:
        The path to id gap look up table.
    energy_phase_table_path:
        The path to id phase look up table.
    source:
        The column name and the name of the source in look up table. e.g. ("source", "idu")
    mode:
        The column name of the mode in look up table.
    min_energy:
        The column name that contain the maximum energy in look up table.
    max_energy:
        The column name that contain the maximum energy in look up table.
    poly_deg:
        The column names for the parameters for the energy conversion polynomial, starting with the least significant.
    prefix:
        Not in use but needed for device_instantiation.
    Name:
        Name of the device
    """

    def __init__(
        self,
        id_gap: UndulatorGap,
        id_phase: UndlatorPhaseAxes,
        energy_gap_table_path: Path,
        energy_phase_table_path: Path,
        source: tuple[str, str] | None = None,
        prefix: str = "",
        mode: str = "Mode",
        min_energy: str = "MinEnergy",
        max_energy: str = "MaxEnergy",
        poly_deg: list | None = None,
        name: str = "",
    ) -> None:
        # A dictionary contains the path to the look up table and the expected column names.
        self.lookup_table_config = {
            "path": {
                "Gap": energy_gap_table_path,
                "Phase": energy_phase_table_path,
            },
            "source": source,
            "mode": mode,
            "min_energy": min_energy,
            "max_energy": max_energy,
            "poly_deg": poly_deg,
        }
        super().__init__(
            id_gap=id_gap,
            id_phase=id_phase,
            prefix=prefix,
            name=name,
        )

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        """
        Check polarisation state and use it together with the energy(value)
        to calculate the required gap and phases before setting it.
        """
        if self.pol is None:
            LOGGER.warning("Polarisation not set attempting to read from hardware")
            pol, phase = await self.determinePhaseFromHardware()
            if pol is None:
                raise ValueError(f"Pol is not set for {self.name}")
            else:
                self.pol = pol

        self._polarisation_set(self.pol)

        gap, phase = self._get_id_gap_phase(value)
        phase3 = -phase if self.pol == "la" else phase
        id_set_val = Apple2Val(
            top_outer=str(phase),
            top_inner="0.0",
            btm_inner=str(phase3),
            btm_outer="0.0",
            gap=str(gap),
        )
        LOGGER.info(f"Setting polarisation to {self.pol}, with {id_set_val}")
        await self._set(value=id_set_val, energy=value)

    def update_lookuptable(self):
        """
        Update the stored lookup tabled from file.

        """
        LOGGER.info("Updating lookup dictionary from file.")
        for key, path in self.lookup_table_config["path"].items():
            if path.exists():
                self.lookup_tables[key] = convert_csv_to_lookup(
                    file=path,
                    source=self.lookup_table_config["source"],
                    mode=self.lookup_table_config["mode"],
                    min_energy=self.lookup_table_config["min_energy"],
                    max_energy=self.lookup_table_config["max_energy"],
                    poly_deg=self.lookup_table_config["poly_deg"],
                )
                # ensure the importing lookup table is the correct format
                Lookuptable.parse_obj(self.lookup_tables[key])
            else:
                raise FileNotFoundError(f"{key} look up table is not in path: {path}")

        self._available_pol = list(self.lookup_tables["Gap"].keys())


class I10Apple2PGM(StandardReadable, Movable):
    """
    Compound device to set both ID and PGM energy at the sample time,
    with the possibility of having id energy offset relative to the pgm.

    Parameters
    ----------
    id:
        An Apple2 device.
    pgm:
        A PGM/mono device.
    prefix:
        Not in use but needed for device_instantiation.
    name:
        New device name.
    """

    def __init__(
        self, id: I10Apple2, pgm: PGM, prefix: str = "", name: str = ""
    ) -> None:
        super().__init__(name=name)
        with self.add_children_as_readables():
            self.id = id
            self.pgm = pgm
        with self.add_children_as_readables(HintedSignal):
            self.energy_offset = soft_signal_rw(float, initial_value=0)

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        LOGGER.info(f"Moving f{self.name} energy to {value}.")
        await asyncio.gather(
            self.id.set(value=value + await self.energy_offset.get_value()),
            self.pgm.energy.set(value),
        )


class I10Apple2Pol(StandardReadable, Movable):
    """
    Compound device to set polorisation of ID.

    Parameters
    ----------
    id:
        An I10Apple2 device.
    prefix:
        Not in use but needed for device_instantiation.
    name:
        New device name.
    """

    def __init__(self, id: I10Apple2, prefix: str = "", name: str = "") -> None:
        super().__init__(name=name)
        with self.add_children_as_readables():
            self.id = id

    @AsyncStatus.wrap
    async def set(self, value: str) -> None:
        self.id.pol = value  # change polarisation.
        LOGGER.info(f"Changing f{self.name} polarisation to {value}.")
        await self.id.set(
            await self.id.energy.get_value()
        )  # Move id to new polarisation


def convert_csv_to_lookup(
    file: str,
    source: tuple[str, str],
    mode: str = "Mode",
    min_energy: str = "MinEnergy",
    max_energy: str = "MaxEnergy",
    poly_deg: list | None = None,
) -> dict[str | None, dict[str, dict[str, dict[str, Any]]]]:
    """
    Convert csv to a dictionary that can be read by Apple2 ID device.

    Parameters
    -----------
    file: str
        File path.
    source: tuple[str, str]
        Tuple(column name, source name)
        e.g. ("Source", "idu").
    mode: str = "Mode"
        Column name for the available modes, "lv","lh","pc","nc" etc
    min_energy: str = "MinEnergy":
        Column name for min energy for the polynomial.
    max_energy: str = "MaxEnergy",
        Column name for max energy for the polynomial.
    poly_deg: list | None = None,
        Column names for the parameters for the polynomial, starting with the least significant.

    return
    ------
        return a dictionary that conform to Apple2 lookup table format:

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
    look_up_table = {}
    pol = []

    def data2dict(row):
        # logical for the conversion for each row of data.
        if row[mode] not in pol:
            pol.append(row[mode])
            look_up_table[row[mode]] = {}
            look_up_table[row[mode]] = {
                "Energies": {},
                "Limit": {
                    "Minimum": float(row[min_energy]),
                    "Maximum": float(row[max_energy]),
                },
            }

        # create polynomial object for energy to gap/phase
        cof = [float(row[x]) for x in poly_deg]
        poly = np.poly1d(cof)

        look_up_table[row[mode]]["Energies"][row[min_energy]] = {
            "Low": float(row[min_energy]),
            "High": float(row[max_energy]),
            "Poly": poly,
        }
        look_up_table[row[mode]]["Limit"]["Minimum"] = min(
            look_up_table[row[mode]]["Limit"]["Minimum"], float(row[min_energy])
        )
        look_up_table[row[mode]]["Limit"]["Maximum"] = max(
            look_up_table[row[mode]]["Limit"]["Maximum"], float(row[max_energy])
        )

    with open(file, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # If there are multiple source only convert requested.
            if row[source[0]] == source[1]:
                data2dict(row=row)
    if not look_up_table:
        raise RuntimeError(f"Unable to convert lookup table:/n/t{file}")
    return look_up_table
