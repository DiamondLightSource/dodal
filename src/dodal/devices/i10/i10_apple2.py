import asyncio
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, SupportsFloat

import numpy as np
from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    soft_signal_r_and_setter,
    soft_signal_rw,
)

from dodal.devices.apple2_undulator import (
    Apple2,
    Apple2Val,
    Lookuptable,
    UndulatorGap,
    UndulatorJawPhase,
    UndulatorPhaseAxes,
)
from dodal.devices.pgm import PGM
from dodal.log import LOGGER

ROW_PHASE_MOTOR_TOLERANCE = 0.004
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100
DEFAULT_JAW_PHASE_POLY_PARAMS = [1.0 / 7.5, -120.0 / 7.5]
ALPHA_OFFSET = 180


# data class to store the lookup table configuration that is use in convert_csv_to_lookup
@dataclass
class LookupPath:
    Gap: Path
    Phase: Path


@dataclass
class LookupTableConfig:
    path: LookupPath
    source: tuple[str, str]
    mode: str | None
    min_energy: str | None
    max_energy: str | None
    poly_deg: list | None


class I10Apple2(Apple2):
    """
    I10Apple2 is the i10 version of Apple2 ID.
    The set and update_lookuptable should be the only part that is I10 specific.

    A pair of look up tables are needed to provide the conversion
     between motor position and energy.
    Set is in energy(eV).
    """

    def __init__(
        self,
        id_gap: UndulatorGap,
        id_phase: UndulatorPhaseAxes,
        id_jaw_phase: UndulatorJawPhase,
        energy_gap_table_path: Path,
        energy_phase_table_path: Path,
        source: tuple[str, str],
        prefix: str = "",
        mode: str = "Mode",
        min_energy: str = "MinEnergy",
        max_energy: str = "MaxEnergy",
        poly_deg: list | None = None,
        name: str = "",
    ) -> None:
        """
        Parameters
        ----------
        id_gap:
            An UndulatorGap device.
        id_phase:
            An UndulatorPhaseAxes device.
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

        # A dataclass contains the path to the look up table and the expected column names.
        self.lookup_table_config = LookupTableConfig(
            path=LookupPath(Gap=energy_gap_table_path, Phase=energy_phase_table_path),
            source=source,
            mode=mode,
            min_energy=min_energy,
            max_energy=max_energy,
            poly_deg=poly_deg,
        )

        super().__init__(
            id_gap=id_gap,
            id_phase=id_phase,
            prefix=prefix,
            name=name,
        )
        with self.add_children_as_readables():
            self.id_jaw_phase = Reference(id_jaw_phase)

    @AsyncStatus.wrap
    async def set(self, value: SupportsFloat) -> None:
        """
        Check polarisation state and use it together with the energy(value)
        to calculate the required gap and phases before setting it.
        """
        value = float(value)
        if self.pol is None:
            LOGGER.warning("Polarisation not set attempting to read from hardware")
            pol, phase = await self.determinePhaseFromHardware()
            if pol is None:
                raise ValueError(f"Pol is not set for {self.name}")
            self.pol = pol

        self._polarisation_set(self.pol)
        gap, phase = self._get_id_gap_phase(value)
        phase3 = phase * (-1 if self.pol == "la" else (1))
        id_set_val = Apple2Val(
            top_outer=str(phase),
            top_inner="0.0",
            btm_inner=str(phase3),
            btm_outer="0.0",
            gap=str(gap),
        )
        LOGGER.info(f"Setting polarisation to {self.pol}, with {id_set_val}")
        await self._set(value=id_set_val, energy=value)
        if self.pol != "la":
            await self.id_jaw_phase().set(0)
            await self.id_jaw_phase().set_move.set(1)

    def update_lookuptable(self):
        """
        Update the stored lookup tabled from file.

        """
        LOGGER.info("Updating lookup dictionary from file.")
        for key, path in self.lookup_table_config.path.__dict__.items():
            if path.exists():
                self.lookup_tables[key] = convert_csv_to_lookup(
                    file=path,
                    source=self.lookup_table_config.source,
                    mode=self.lookup_table_config.mode,
                    min_energy=self.lookup_table_config.min_energy,
                    max_energy=self.lookup_table_config.max_energy,
                    poly_deg=self.lookup_table_config.poly_deg,
                )
                # ensure the importing lookup table is the correct format
                Lookuptable.model_validate(self.lookup_tables[key])
            else:
                raise FileNotFoundError(f"{key} look up table is not in path: {path}")

        self._available_pol = list(self.lookup_tables["Gap"].keys())


class I10Apple2PGM(StandardReadable, Movable[float]):
    """
    Compound device to set both ID and PGM energy at the sample time,poly_deg

    """

    def __init__(
        self, id: I10Apple2, pgm: PGM, prefix: str = "", name: str = ""
    ) -> None:
        """
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
        super().__init__(name=name)
        self.id_ref = Reference(id)
        self.pgm_ref = Reference(pgm)
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.energy_offset = soft_signal_rw(float, initial_value=0)

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        LOGGER.info(f"Moving f{self.name} energy to {value}.")
        await asyncio.gather(
            self.id_ref().set(value=value + await self.energy_offset.get_value()),
            self.pgm_ref().energy.set(value),
        )


class I10Apple2Pol(StandardReadable, Movable[str]):
    """
    Compound device to set polorisation of ID.
    """

    def __init__(self, id: I10Apple2, prefix: str = "", name: str = "") -> None:
        """
        Parameters
        ----------
        id:
            An I10Apple2 device.
        prefix:
            Not in use but needed for device_instantiation.
        name:
            New device name.
        """
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


class LinearArbitraryAngle(StandardReadable, Movable[SupportsFloat]):
    """
    Device to set polorisation angle of the ID. Linear Arbitrary Angle (laa)
     is the direction of the magnetic field which can be change by varying the jaw_phase
     in (linear arbitrary (la) mode,
     The angle of 0 is equivalent to linear horizontal "lh" (sigma) and
      90 is linear vertical "lv" (pi).
    This device require a jaw_phase to angle conversion which is done via a polynomial.
    """

    def __init__(
        self,
        id: I10Apple2,
        prefix: str = "",
        name: str = "",
        jaw_phase_limit: float = 12.0,
        jaw_phase_poly_param: list[float] = DEFAULT_JAW_PHASE_POLY_PARAMS,
        angle_threshold_deg=30.0,
    ) -> None:
        """
        Parameters
        ----------
        id: I10Apple2
            An I10Apple2 device.
        prefix: str
            Not in use but needed for device_instantiation.
        name: str
            New device name.
        jaw_phase_limit: float
            The maximum allowed jaw_phase movement.
        jaw_phase_poly_param: list
            polynomial parameters highest power first.
        """
        super().__init__(name=name)
        self.id_ref = Reference(id)
        self.jaw_phase_from_angle = np.poly1d(jaw_phase_poly_param)
        self.angle_threshold_deg = angle_threshold_deg
        self.jaw_phase_limit = jaw_phase_limit
        with self.add_children_as_readables(StandardReadableFormat.HINTED_SIGNAL):
            self.angle, self._angle_set = soft_signal_r_and_setter(
                float, initial_value=None
            )

    @AsyncStatus.wrap
    async def set(self, value: SupportsFloat) -> None:
        value = float(value)
        pol = self.id_ref().pol
        if pol != "la":
            raise RuntimeError(
                f"Angle control is not available in polarisation {pol} with {self.id_ref().name}"
            )
        # Moving to real angle which is 210 to 30.
        alpha_real = value if value > self.angle_threshold_deg else value + ALPHA_OFFSET
        jaw_phase = self.jaw_phase_from_angle(alpha_real)
        if abs(jaw_phase) > self.jaw_phase_limit:
            raise RuntimeError(
                f"jaw_phase position for angle ({value}) is outside permitted range"
                f" [-{self.jaw_phase_limit}, {self.jaw_phase_limit}]"
            )
        await self.id_ref().id_jaw_phase().set(jaw_phase)
        self._angle_set(value)


def convert_csv_to_lookup(
    file: str,
    source: tuple[str, str],
    mode: str | None = "Mode",
    min_energy: str | None = "MinEnergy",
    max_energy: str | None = "MaxEnergy",
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

    def data2dict(row) -> None:
        # logic for the conversion for each row of data.
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
