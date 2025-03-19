import asyncio
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, SupportsFloat

import numpy as np
from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    Device,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    soft_signal_r_and_setter,
    soft_signal_rw,
)

from dodal.log import LOGGER

# from dodal.beamlines.i10 import pgm
from ..apple2_undulator import (
    Apple2,
    Apple2Val,
    Lookuptable,
    Pol,
    UndulatorGap,
    UndulatorJawPhase,
    UndulatorPhaseAxes,
)
from ..pgm import PGM

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
    """I10Apple2 is the i10 version of Apple2 ID, set and update_lookuptable function
    should be the only part that is I10 specific.

    A pair of look up tables are needed to provide the conversion between motor position and energy.

    Set is in energy(eV).
    """

    def __init__(
        self,
        look_up_table_dir: str,
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
        look_up_table_dir:
            The path to look up table.
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
            epic pv for id
        Name:
            Name of the device
        """

        energy_gap_table_path = Path(
            look_up_table_dir + "IDEnergy2GapCalibrations.csv",
        )
        energy_phase_table_path = Path(
            look_up_table_dir + "IDEnergy2PhaseCalibrations.csv",
        )
        # A dataclass contains the path to the look up table and the expected column names.
        self.lookup_table_config = LookupTableConfig(
            path=LookupPath(Gap=energy_gap_table_path, Phase=energy_phase_table_path),
            source=source,
            mode=mode,
            min_energy=min_energy,
            max_energy=max_energy,
            poly_deg=poly_deg,
        )

        with self.add_children_as_readables():
            super().__init__(
                id_gap=UndulatorGap(name="id_gap", prefix=prefix),
                id_phase=UndulatorPhaseAxes(
                    name="id_phase",
                    prefix=prefix,
                    top_outer="RPQ1",
                    top_inner="RPQ2",
                    btm_inner="RPQ3",
                    btm_outer="RPQ4",
                ),
                prefix=prefix,
                name=name,
            )
            self.id_jaw_phase = UndulatorJawPhase(
                prefix=prefix,
                move_pv="RPQ1",
            )

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        """
        Check polarisation state and use it together with the energy(value)
        to calculate the required gap and phases before setting it.
        """
        pol = await self.polarisation_setpoint.get_value()
        if pol.value == Pol.NONE:
            LOGGER.warning("Polarisation not set attempting to read from hardware")
            pol, phase = await self.determine_phase_from_hardware()
            if pol.value == "None":
                raise ValueError(
                    f"Polarisation cannot be determine from hardware for {self.name}"
                )
            self._polarisation_setpoint_set(pol)
        gap, phase = await self._get_id_gap_phase(value)
        phase3 = phase * (-1 if pol == "la" else (1))
        id_set_val = Apple2Val(
            top_outer=f"{phase:.6f}",
            top_inner="0.0",
            btm_inner=f"{phase3:.6f}",
            btm_outer="0.0",
            gap=f"{gap:.6f}",
        )
        LOGGER.info(f"Setting polarisation to {pol}, with {id_set_val}")
        await self._set(value=id_set_val, energy=value)
        if pol != "la":
            await self.id_jaw_phase.set(0)
            await self.id_jaw_phase.set_move.set(1)

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


class EnergySetter(StandardReadable, Movable):
    """
    Compound device to set both ID and PGM energy at the same time.

    """

    def __init__(self, id: I10Apple2, pgm: PGM, name: str = "") -> None:
        """
        Parameters
        ----------
        id:
            An Apple2 device.
        pgm:
            A PGM/mono device.
        name:
            New device name.
        """
        super().__init__(name=name)
        self.id = id
        self.pgm_ref = Reference(pgm)

        self.add_readables(
            [self.id.energy, self.pgm_ref().energy.user_readback],
            StandardReadableFormat.HINTED_SIGNAL,
        )

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.energy_offset = soft_signal_rw(float, initial_value=0)

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        LOGGER.info(f"Moving f{self.name} energy to {value}.")
        await asyncio.gather(
            self.id.set(value=value + await self.energy_offset.get_value()),
            self.pgm_ref().energy.set(value),
        )


class I10Apple2Pol(StandardReadable, Movable):
    """
    Compound device to set polorisation of ID.
    """

    def __init__(self, id: I10Apple2, name: str = "") -> None:
        """
        Parameters
        ----------
        id:
            An I10Apple2 device.
        name:
            New device name.
        """
        super().__init__(name=name)
        self.id_ref = Reference(id)
        self.add_readables([self.id_ref().polarisation_readback])

    @AsyncStatus.wrap
    async def set(self, value: Pol) -> None:
        # Check before set
        self.id_ref().set_pol(value)
        LOGGER.info(f"Changing f{self.name} polarisation to {value}.")
        await self.id_ref().set(
            await self.id_ref().energy.get_value()
        )  # Move id to new polarisation


class LinearArbitraryAngle(StandardReadable, Movable):
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
        pol = await self.id_ref().polarisation_readback.get_value()
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
        await self.id_ref().id_jaw_phase.set(jaw_phase)
        self._angle_set(value)


class I10Id(Device):
    def __init__(
        self,
        pgm: PGM,
        prefix: str,
        look_up_table_dir: str,
        source: tuple[str, str],
        jaw_phase_limit=12.0,
        jaw_phase_poly_param=DEFAULT_JAW_PHASE_POLY_PARAMS,
        angle_threshold_deg=30.0,
        name: str = "",
    ) -> None:
        """A compound device to make up the full I10 insertion device.
         This is in effect a single I10Apple2 with three different set methods for
         energy, polarisation and linear arbitrary angle. See
         `UML </_images/i10_id_design.png>`__ for detail.
        .. figure:: /explanations/umls/i10_id_design.png
        Attributes
        ----------
            energy: EnergySetter
                Devices that move both pgm and id energy at the same time.
            pol: I10Apple2Pol
                Devices that control the x-ray polarisation.
            laa: LinearArbitraryAngle
                Devices that allow alteration of the beam polarisation angle in LA mode.
        """
        self.energy = EnergySetter(
            id=I10Apple2(
                look_up_table_dir=look_up_table_dir,
                name="id_energy",
                source=source,
                prefix=prefix,
            ),
            pgm=pgm,
            name="energy",
        )
        self.pol = I10Apple2Pol(id=self.energy.id, name="pol")
        self.laa = LinearArbitraryAngle(
            id=self.energy.id,
            name="laa",
            jaw_phase_limit=jaw_phase_limit,
            jaw_phase_poly_param=jaw_phase_poly_param,
            angle_threshold_deg=angle_threshold_deg,
        )

        super().__init__(name=name)


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
        return a dictionary that conform to Apple2 lookup table format: Lookuptable
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
