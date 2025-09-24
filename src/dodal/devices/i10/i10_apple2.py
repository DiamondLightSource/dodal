import asyncio
import csv
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any, SupportsFloat

import numpy as np
from bluesky.protocols import Movable
from daq_config_server.client import ConfigServer
from ophyd_async.core import (
    AsyncStatus,
    Device,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    soft_signal_r_and_setter,
    soft_signal_rw,
)
from pydantic import BaseModel, ConfigDict, RootModel

from dodal.log import LOGGER

from ..apple2_undulator import (
    Apple2,
    Apple2Val,
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
MAXIMUM_MOVE_TIME = 550  # There is no useful movements take longer than this.


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


class I10Apple2(Apple2):
    """I10Apple2 is the i10 version of Apple2 ID, set and update_lookuptable function
    should be the only part that is I10 specific.

    A pair of look up tables are needed to provide the conversion betwApple 2 ID/undulator has 4 extra degrees of freedom compare to the standard Undulator,
    each bank of magnet can move independently to each other,
    which allow the production of different x-ray polarisation as well as energy.
    This type of ID is use on I10, I21, I09, I17 and I06 for soft x-ray.een motor position and energy.

    Set is in energy(eV).
    """

    def __init__(
        self,
        look_up_table_dir: str,
        source: tuple[str, str],
        prefix: str,
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

        self.i10_look_up_table_client = IdConfigureClient(
            look_up_table_dir=look_up_table_dir,
            source=(source),
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
                name=name,
            )
            self.id_jaw_phase = UndulatorJawPhase(
                prefix=prefix,
                move_pv="RPQ1",
            )
        # self.update_lookuptable()

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        """
        Check polarisation state and use it together with the energy(value)
        to calculate the required gap and phases before setting it.
        """

        pol = await self.polarisation_setpoint.get_value()

        if pol == Pol.NONE:
            LOGGER.warning(
                "Found no setpoint for polarisation. Attempting to"
                " determine polarisation from hardware..."
            )
            pol = await self.polarisation.get_value()
            if pol == Pol.NONE:
                raise ValueError(
                    f"Polarisation cannot be determined from hardware for {self.name}"
                )

            self._set_pol_setpoint(pol)
        gap, phase = await self._get_id_gap_phase(energy=value, pol=pol)
        phase3 = phase * (-1 if pol == Pol.LA else 1)
        id_set_val = Apple2Val(
            top_outer=f"{phase:.6f}",
            top_inner="0.0",
            btm_inner=f"{phase3:.6f}",
            btm_outer="0.0",
            gap=f"{gap:.6f}",
        )

        LOGGER.info(f"Setting polarisation to {pol}, with values: {id_set_val}")
        await self._set(value=id_set_val, energy=value)
        if pol != Pol.LA:
            await self.id_jaw_phase.set(0)
            await self.id_jaw_phase.set_move.set(1)
        LOGGER.info(f"Energy set to {value} eV successfully.")

    async def _get_id_gap_phase(self, energy: float, pol: Pol) -> tuple[float, float]:
        """
        Converts energy and polarisation to gap and phase.
        """

        return self.i10_look_up_table_client.get_motor_from_energy(
            energy=energy, pol=pol
        )

    async def _get_poly(
        self,
        new_energy: float,
        pol: Pol,
        lookup_table: dict[str | None, dict[str, dict[str, Any]]],
    ) -> np.poly1d:
        """
        Get the correct polynomial for a given energy form lookuptable
        for the current polarisation setpoint.
        Parameters
        ----------
        new_energy : float
            The energy in eV for which the polynomial is requested.
        lookup_table : dict[str | None, dict[str, dict[str, Any]]]
            The lookup table containing polynomial coefficients for different energies
            and polarisations.
        Returns
        -------
        np.poly1d
            The polynomial coefficients for the requested energy and polarisation.
        Raises
        ------
        ValueError
            If the requested energy is outside the limits defined in the lookup table
            or if no polynomial coefficients are found for the requested energy.
        """
        # pol = await self.polarisation_setpoint.get_value()
        if (
            new_energy < lookup_table[pol]["Limit"]["Minimum"]
            or new_energy > lookup_table[pol]["Limit"]["Maximum"]
        ):
            raise ValueError(
                "Demanding energy must lie between {} and {} eV!".format(
                    lookup_table[pol]["Limit"]["Minimum"],
                    lookup_table[pol]["Limit"]["Maximum"],
                )
            )
        else:
            for energy_range in lookup_table[pol]["Energies"].values():
                if (
                    new_energy >= energy_range["Low"]
                    and new_energy < energy_range["High"]
                ):
                    return energy_range["Poly"]

        raise ValueError(
            """Cannot find polynomial coefficients for your requested energy.
        There might be gap in the calibration lookup table."""
        )


class EnergySetter(StandardReadable, Movable[float]):
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


class I10Apple2Pol(StandardReadable, Movable[Pol]):
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
        self.add_readables([self.id_ref().polarisation])

    @AsyncStatus.wrap
    async def set(self, value: Pol) -> None:
        LOGGER.info(f"Changing f{self.name} polarisation to {value}.")
        # Timeout is determined internally by the set method later, so we set it to max here.
        await self.id_ref().polarisation.set(value, timeout=MAXIMUM_MOVE_TIME)


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
        pol = await self.id_ref().polarisation.get_value()
        if pol != Pol.LA:
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
        """I10Id is a compound device that combines the I10-specific Apple2 undulator,
        energy setter, and polarization control.
        This class provides a high-level interface for controlling the undulator's
        energy, polarization, and linear arbitrary angle.

        Attributes
        ----------
        id : I10Apple2
            The I10-specific Apple2 undulator device.
        energy_setter : EnergySetter
            A device for synchronizing the undulator and monochromator energy.
        pol : I10Apple2Pol
            A device for controlling the polarization of the undulator.
        linear_arbitrary_angle : LinearArbitraryAngle
            A device for controlling the linear arbitrary polarization angle.
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


class IdConfigureClient(ConfigServer):
    def __init__(
        self,
        look_up_table_dir: str,
        source: tuple[str, str],
        mode: str = "Mode",
        min_energy: str = "MinEnergy",
        max_energy: str = "MaxEnergy",
        poly_deg: list | None = None,
        url: str = "https://daq-config.diamond.ac.uk",
    ):
        self.lookup_tables: dict[str, dict[str | None, dict[str, dict[str, Any]]]] = {
            "Gap": {},
            "Phase": {},
        }
        energy_gap_table_path = Path(look_up_table_dir, "IDEnergy2GapCalibrations.csv")
        energy_phase_table_path = Path(
            look_up_table_dir, "IDEnergy2PhaseCalibrations.csv"
        )
        self.lookup_table_config = LookupTableConfig(
            path=LookupPath(Gap=energy_gap_table_path, Phase=energy_phase_table_path),
            source=source,
            mode=mode,
            min_energy=min_energy,
            max_energy=max_energy,
            poly_deg=poly_deg,
        )
        super().__init__(url)
        self._available_pol = []

    def _get_lookup_table(self, lookup_table_path: Path | str):
        return self.get_file_contents(lookup_table_path)

    def update_lookuptable(self):
        """
        Update the stored lookup tabled from file.

        """
        LOGGER.info("Updating lookup dictionary from file.")
        for key, path in self.lookup_table_config.path.__dict__.items():
            if path.exists():
                self.lookup_tables[key] = self.convert_csv_to_lookup(
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

    def get_motor_from_energy(self, energy: float, pol: Pol) -> tuple[float, float]:
        """
        Converts energy and polarisation to gap and phase.
        """
        gap_poly = self._get_poly(
            lookup_table=self.lookup_tables["Gap"], new_energy=energy, pol=pol
        )
        phase_poly = self._get_poly(
            lookup_table=self.lookup_tables["Phase"], new_energy=energy, pol=pol
        )
        return gap_poly(energy), phase_poly(energy)

    def _get_poly(
        self,
        new_energy: float,
        pol: Pol,
        lookup_table: dict[str | None, dict[str, dict[str, Any]]],
    ) -> np.poly1d:
        """
        Get the correct polynomial for a given energy form lookuptable
        for the current polarisation setpoint.
        Parameters
        ----------
        new_energy : float
            The energy in eV for which the polynomial is requested.
        lookup_table : dict[str | None, dict[str, dict[str, Any]]]
            The lookup table containing polynomial coefficients for different energies
            and polarisations.
        Returns
        -------
        np.poly1d
            The polynomial coefficients for the requested energy and polarisation.
        Raises
        ------
        ValueError
            If the requested energy is outside the limits defined in the lookup table
            or if no polynomial coefficients are found for the requested energy.
        """
        if (
            new_energy < lookup_table[pol]["Limit"]["Minimum"]
            or new_energy > lookup_table[pol]["Limit"]["Maximum"]
        ):
            raise ValueError(
                "Demanding energy must lie between {} and {} eV!".format(
                    lookup_table[pol]["Limit"]["Minimum"],
                    lookup_table[pol]["Limit"]["Maximum"],
                )
            )
        else:
            for energy_range in lookup_table[pol]["Energies"].values():
                if (
                    new_energy >= energy_range["Low"]
                    and new_energy < energy_range["High"]
                ):
                    return energy_range["Poly"]

        raise ValueError(
            """Cannot find polynomial coefficients for your requested energy.
        There might be gap in the calibration lookup table."""
        )

    def convert_csv_to_lookup(
        self,
        file: str,
        source: tuple[str, str],
        mode: str | None = "Mode",
        min_energy: str | None = "MinEnergy",
        max_energy: str | None = "MaxEnergy",
        poly_deg: list | None = None,
    ) -> dict[str | None, dict[str, dict[str, dict[str, Any]]]]:
        """
        Convert a CSV file to a dictionary compatible with the Apple2 lookup table format.

        Parameters
        ----------
        file : str
            Path to the CSV file.
        source : tuple[str, str]
            Tuple specifying the column name and source name (e.g., ("Source", "idu")).
        mode : str, optional
            Column name for the available modes (e.g., "lv", "lh", "pc", "nc"), by default "Mode".
        min_energy : str, optional
            Column name for the minimum energy, by default "MinEnergy".
        max_energy : str, optional
            Column name for the maximum energy, by default "MaxEnergy".
        poly_deg : list, optional
            Column names for polynomial coefficients, starting with the least significant term.

        Returns
        -------
        dict
            A dictionary conforming to the Apple2 lookup table format.

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
        lookup_table = {}
        polarisations = set()

        def process_row(row: dict) -> None:
            """Process a single row from the CSV file and update the lookup table."""
            mode_value = row[mode]
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

        csvfile = self.get_file_contents(file)
        reader = csv.DictReader(io.StringIO(csvfile))
        for row in reader:
            print(row)
            # If there are multiple source only convert requested.
            if row[source[0]] == source[1]:
                process_row(row=row)
        if not lookup_table:
            raise RuntimeError(f"Unable to convert lookup table:/n/t{file}")
        return lookup_table
