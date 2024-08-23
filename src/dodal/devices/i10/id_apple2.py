import asyncio
import csv
from pathlib import Path

import numpy as np
from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    HintedSignal,
    StandardReadable,
    soft_signal_r_and_setter,
    soft_signal_rw,
    wait_for_value,
)

from dodal.devices.apple2_undulator import (
    Apple2Val,
    UndlatorPhaseAxes,
    UndulatorGap,
    UndulatorGatestatus,
)
from dodal.devices.monochromator import PGM
from dodal.log import LOGGER

ROW_PHASE_MOTOR_TOLERANCE = 0.004
MAXIMUM_ROW_PHASE_MOTOR_POSITION = 24.0
MAXIMUM_GAP_MOTOR_POSITION = 100


class I10Apple2(StandardReadable, Movable):
    """
    Apple2 id with both phase and gap motion for i10(Only part that is kind of I10 specific is the set).
    A pair of look up tables are needed to provide the conversion between motor position and energy.
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
    max_energy: str = "MaxEnergy",
        The column name that contain the maximum energy in look up table.
    poly_deg:
        The column names for the parameters for the energy conversion polynomial, starting with the least significant.
    prefix:
        Not in use but needed for device_instantiation.
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
        super().__init__(name)

        # Attributes are set after super call so they are not renamed to
        # <name>-undulator, etc.
        with self.add_children_as_readables():
            self.gap = id_gap
            self.phase = id_phase
        with self.add_children_as_readables(HintedSignal):
            # Store the polarisation for readback.
            self.polarisation, self._polarisation_set = soft_signal_r_and_setter(
                str, initial_value=None
            )
            # Store the set energy for readback.
            self.energy, self._energy_set = soft_signal_r_and_setter(
                float, initial_value=None
            )

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
        self.lookup_tables = {}
        self._available_pol = []
        self._pol = None
        # Run at start up to load lookup tables and set available_pol.
        self.update_poly()

    @property
    def pol(self):
        return self._pol

    @pol.setter
    def pol(self, pol: str):
        # This set the pol but does not actually move hardware.
        if pol in self._available_pol:
            self._pol = pol
        else:
            raise ValueError(
                f"Polarisation {pol} is not available:"
                + f"/n Polarisations available:  {self._available_pol}"
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
        LOGGER.info(f"Seting polarisation to {self.pol}, with {id_set_val}")
        await self._set(value=id_set_val, energy=value)

    async def _set(self, value: Apple2Val, energy: float) -> None:
        """
        Check ID is in a movable state and set all the demand value before moving.

        """

        # Only need to check gap as the phase motors share both fault and gate with gap.
        if await self.gap.fault.get_value() != 0:
            raise RuntimeError(f"{self.name} is in fault state")
        if await self.gap.gate.get_value() != UndulatorGatestatus.close:
            raise RuntimeError(f"{self.name} is already in motion.")
        await asyncio.gather(
            self.phase.top_outer.user_setpoint.set(value=value.top_outer),
            self.phase.top_inner.user_setpoint.set(value=value.top_inner),
            self.phase.btm_inner.user_setpoint.set(value=value.btm_inner),
            self.phase.btm_outer.user_setpoint.set(value=value.btm_outer),
            self.gap.user_setpoint.set(value=value.gap),
        )
        timeout = np.max(
            await asyncio.gather(self.gap.get_timeout(), self.phase.get_timeout())
        )
        LOGGER.info(
            f"Moving f{self.name} energy and polorisation to {energy}, {self.pol}"
            + f"with motor position {value}, timeout = {timeout}"
        )
        await self.gap.set_move.set(value=1)
        await wait_for_value(self.gap.gate, UndulatorGatestatus.close, timeout=timeout)
        self._energy_set(energy)  # Update energy for after move for readback.

    def _get_id_gap_phase(self, energy) -> tuple[float, float]:
        """
        Converts energy and polarisation to gap and phase.
        """
        gap_poly = self._get_poly(
            lookup_table=self.lookup_tables["Gap"], new_energy=energy
        )
        phase_poly = self._get_poly(
            lookup_table=self.lookup_tables["Phase"], new_energy=energy
        )
        return gap_poly(energy), phase_poly(energy)

    def _get_poly(self, new_energy, lookup_table) -> np.poly1d:
        """
        Get the correct polynomial for a given energy.
        """

        if (
            new_energy < lookup_table[self.pol]["Limit"]["Minimum"]
            or new_energy > lookup_table[self.pol]["Limit"]["Maximum"]
        ):
            raise ValueError(
                "Demanding energy must lie between {} and {} eV!".format(
                    lookup_table[self.pol]["Limit"]["Minimum"],
                    lookup_table[self.pol]["Limit"]["Maximum"],
                )
            )
        else:
            for energy_range in lookup_table[self.pol]["Energies"].values():
                if (
                    new_energy >= energy_range["Low"]
                    and new_energy < energy_range["High"]
                ):
                    return energy_range["Poly"]

        raise ValueError(
            "Cannot find polynomial coefficients for your requested energy."
            + "There might be gap in the calibration lookup table."
        )

    def update_poly(self):
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
            else:
                raise FileNotFoundError(f"{key} look up table is not in path: {path}")
        self._available_pol = list(self.lookup_tables["Gap"].keys())

    def _motorPositionEqual(self, a, b):
        return abs(a - b) < ROW_PHASE_MOTOR_TOLERANCE

    async def determinePhaseFromHardware(self) -> tuple[str | None, float]:
        """
        Try to determine polarisation and phase value using row phase motor position pattern.
        However there is no way to return lh3 polarisation or higher harmonic setting.
        (May be for future one can use the inverse poly to work out the energy and try to match it with the current energy
        to workout the polarisation but during my test the inverse poly is too unstable for general use.)
        """
        cur_loc = await self.read()
        top_outer = cur_loc[self.phase.top_outer.user_setpoint_readback.name]["value"]
        top_inner = cur_loc[self.phase.top_inner.user_setpoint_readback.name]["value"]
        btm_inner = cur_loc[self.phase.btm_inner.user_setpoint_readback.name]["value"]
        btm_outer = cur_loc[self.phase.btm_outer.user_setpoint_readback.name]["value"]
        gap = cur_loc[self.gap.user_readback.name]["value"]
        if gap > MAXIMUM_GAP_MOTOR_POSITION:
            raise RuntimeError(
                f"{self.name} is not in use, close gap or set polarisation to use this ID"
            )

        if (
            self._motorPositionEqual(top_outer, 0.0)
            and self._motorPositionEqual(top_inner, 0.0)
            and self._motorPositionEqual(btm_inner, 0.0)
            and self._motorPositionEqual(btm_outer, 0.0)
        ):
            # Linear Horizontal
            polarisation = "lh"
            phase = 0.0
            return polarisation, phase
        if (
            self._motorPositionEqual(top_outer, MAXIMUM_ROW_PHASE_MOTOR_POSITION)
            and self._motorPositionEqual(top_inner, 0.0)
            and self._motorPositionEqual(btm_inner, MAXIMUM_ROW_PHASE_MOTOR_POSITION)
            and self._motorPositionEqual(btm_outer, 0.0)
        ):
            # Linear Vertical
            polarisation = "lv"
            phase = MAXIMUM_ROW_PHASE_MOTOR_POSITION
            return polarisation, phase
        if (
            self._motorPositionEqual(top_outer, btm_inner)
            and top_outer > 0.0
            and self._motorPositionEqual(top_inner, 0.0)
            and self._motorPositionEqual(btm_outer, 0.0)
        ):
            # Positive Circular
            polarisation = "pc"
            phase = top_outer
            return polarisation, phase
        if (
            self._motorPositionEqual(top_outer, btm_inner)
            and top_outer < 0.0
            and self._motorPositionEqual(top_inner, 0.0)
            and self._motorPositionEqual(btm_outer, 0.0)
        ):
            # Negative Circular
            polarisation = "nc"
            phase = top_outer
            return polarisation, phase
        if (
            self._motorPositionEqual(top_outer, -btm_inner)
            and self._motorPositionEqual(top_inner, 0.0)
            and self._motorPositionEqual(btm_outer, 0.0)
        ):
            # Positive Linear Arbitrary
            polarisation = "la"
            phase = top_outer
            return polarisation, phase
        if (
            self._motorPositionEqual(top_inner, -btm_outer)
            and self._motorPositionEqual(top_outer, 0.0)
            and self._motorPositionEqual(btm_inner, 0.0)
        ):
            # Negative Linear Arbitrary
            polarisation = "la"
            phase = top_inner
            return polarisation, phase
        # UNKNOWN default
        polarisation = None
        phase = 0.0
        return (polarisation, phase)


class I10Apple2PGM(StandardReadable, Movable):
    """
    Compound device to set both ID and PGM energy at the sample time,
    with the possibility of having id energy offset relative to the pgm.

    Parameters
    ----------
    id:
        An I10Apple2 device.
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
):
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
            look_up_table[row[mode]]["Energies"] = {}
            look_up_table[row[mode]]["Limit"] = {}
            look_up_table[row[mode]]["Limit"]["Minimum"] = float(row[min_energy])
            look_up_table[row[mode]]["Limit"]["Maximum"] = float(row[max_energy])
        # create polynomial object for energy to gap/phase
        cof = [float(row[x]) for x in poly_deg]
        poly = np.poly1d(cof)

        look_up_table[row[mode]]["Energies"][row[min_energy]] = {
            "Low": float(row[min_energy]),
            "High": float(row[max_energy]),
            "Poly": poly,
        }
        if look_up_table[row[mode]]["Limit"]["Minimum"] > float(row[min_energy]):
            look_up_table[row[mode]]["Limit"]["Minimum"] = float(row[min_energy])
        if look_up_table[row[mode]]["Limit"]["Maximum"] < float(row[min_energy]):
            look_up_table[row[mode]]["Limit"]["Maximum"] = float(row[max_energy])

    with open(file, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # If there are multiple source only convert requested.
            if row[source[0]] == source[1]:
                data2dict(row=row)
    if not look_up_table:
        raise RuntimeError(f"Unable to convert lookup table:/n/t{file}")
    return look_up_table
