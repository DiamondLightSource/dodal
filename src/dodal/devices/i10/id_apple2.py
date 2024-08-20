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
    Apple2 id with both phase and gap motion for i10.
    A pair of look up tables are needed to provide the conversion between motor position and energy.
    Set is in energy in eV.
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
        with self.add_children_as_readables():
            self.gap = id_gap
            self.phase = id_phase
        with self.add_children_as_readables(HintedSignal):
            # Store the polarisation for readback
            self.polarisation, self._polarisation_set = soft_signal_r_and_setter(
                str, initial_value=None
            )
            # Store the set energy for readback
            self.energy, self._energy_set = soft_signal_r_and_setter(
                float, initial_value=None
            )

        super().__init__(name)
        # The path to the look up table and teh column names expected.
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
        self._startup()

    def _startup(self):
        self.update_poly()
        self._available_pol = list(self.lookup_tables["Gap"].keys())
        self._pol = None

    @property
    def pol(self):
        return self._pol

    @pol.setter
    def pol(self, pol: str):
        if pol in self._available_pol:
            self._pol = pol
        else:
            raise ValueError(
                f"Polarisation {pol} is not available:"
                + f"/n Polarisations available:  {self._available_pol}"
            )

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        if self.pol is None:
            LOGGER.info("Polarisation not set attempting to read from hardware")
            pol, phase = await self.determinePhaseFromHardware()
            if pol is None:
                raise ValueError(f"Pol is not set for {self.name} and ")
            else:
                self.pol = pol
        LOGGER.info(f"Seting polarisation to {self.pol}")
        self._polarisation_set(self.pol)

        gap, phase = self._get_id_gap_phase(value)
        id_set_val = Apple2Val(
            top_outer=str(phase),
            top_inner="0.0",
            btm_inner=str(-phase),
            btm_outer="0.0",
            gap=str(gap),
        )
        await self._set(value=id_set_val, energy=value)

    @AsyncStatus.wrap
    async def _set(self, value: Apple2Val, energy: float) -> None:
        # Only need to check gap as the phase motors share both fault and gate with gap.
        if await self.gap.fault.get_value() != 0:
            raise RuntimeError(f"{self.name} is in fault state")
        if await self.gap.gate.get_value() != UndulatorGatestatus.close:
            raise RuntimeError(f"{self.name} is already in motion.")
        await asyncio.gather(
            self.phase.top_outer.user_setpoint.set(value=value.top_outer),
            self.phase.top_inner.user_setpoint.set(value=value.top_inner),
            self.phase.btm_outer.user_setpoint.set(value=value.btm_outer),
            self.phase.btm_inner.user_setpoint.set(value=value.btm_inner),
            self.gap.user_setpoint.set(value=value.gap),
        )
        timeout = np.max(
            await asyncio.gather(self.gap.get_timeout(), self.phase.get_timeout())
        )
        LOGGER.info(
            f"Moving f{self.name} energy to {energy} with {value}, timeout = {timeout}"
        )
        await self.gap.set_move.set(value=1)
        await wait_for_value(self.gap.gate, UndulatorGatestatus.close, timeout=timeout)
        self._energy_set(energy)

    def _get_id_gap_phase(self, energy) -> tuple[float, float]:
        """
        Converts energy and polarisation to  gap and phase.
        """
        gap_poly = self._get_poly(
            lookup_table=self.lookup_tables["Gap"], new_energy=energy
        )
        phase_poly = self._get_poly(
            lookup_table=self.lookup_tables["Phase"], new_energy=energy
        )
        return gap_poly(energy), phase_poly(energy)

    def _get_poly(self, new_energy, lookup_table) -> np.poly1d:
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
                print(energy_range)
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

    def _motorPositionEqual(self, a, b):
        return abs(a - b) < ROW_PHASE_MOTOR_TOLERANCE

    async def determinePhaseFromHardware(self) -> tuple[str | None, float]:
        cur_loc = await self.read()
        rowphase1 = cur_loc[self.phase.top_inner.user_setpoint_readback.name]["value"]
        rowphase2 = cur_loc[self.phase.top_outer.user_setpoint_readback.name]["value"]
        rowphase3 = cur_loc[self.phase.btm_inner.user_setpoint_readback.name]["value"]
        rowphase4 = cur_loc[self.phase.btm_outer.user_setpoint_readback.name]["value"]
        gap = cur_loc[self.gap.user_readback.name]["value"]
        if gap > MAXIMUM_GAP_MOTOR_POSITION:
            raise RuntimeError(
                f"{self.name} is not in use, close gap or set polarisation to use this ID"
            )
        # determine polarisation and phase value using row phase motor position pattern, However there is no way to return lh3 polarisation
        if (
            self._motorPositionEqual(rowphase1, 0.0)
            and self._motorPositionEqual(rowphase2, 0.0)
            and self._motorPositionEqual(rowphase3, 0.0)
            and self._motorPositionEqual(rowphase4, 0.0)
        ):
            # Linear Horizontal
            polarisation = "lh"
            phase = 0.0
            return polarisation, phase
        if (
            self._motorPositionEqual(rowphase1, MAXIMUM_ROW_PHASE_MOTOR_POSITION)
            and self._motorPositionEqual(rowphase2, 0.0)
            and self._motorPositionEqual(rowphase3, MAXIMUM_ROW_PHASE_MOTOR_POSITION)
            and self._motorPositionEqual(rowphase4, 0.0)
        ):
            # Linear Vertical
            polarisation = "lv"
            phase = MAXIMUM_ROW_PHASE_MOTOR_POSITION
            return polarisation, phase
        if (
            self._motorPositionEqual(rowphase1, rowphase3)
            and rowphase1 > 0.0
            and self._motorPositionEqual(rowphase2, 0.0)
            and self._motorPositionEqual(rowphase4, 0.0)
        ):
            # Positive Circular
            polarisation = "pc"
            phase = rowphase1
            return polarisation, phase
        if (
            self._motorPositionEqual(rowphase1, rowphase3)
            and rowphase1 < 0.0
            and self._motorPositionEqual(rowphase2, 0.0)
            and self._motorPositionEqual(rowphase4, 0.0)
        ):
            # Negative Circular
            polarisation = "nc"
            phase = rowphase1
            return polarisation, phase
        if (
            self._motorPositionEqual(rowphase1, -rowphase3)
            and self._motorPositionEqual(rowphase2, 0.0)
            and self._motorPositionEqual(rowphase4, 0.0)
        ):
            # Positive Linear Arbitrary
            polarisation = "la"
            phase = rowphase1
            return polarisation, phase
        if (
            self._motorPositionEqual(rowphase2, -rowphase4)
            and self._motorPositionEqual(rowphase1, 0.0)
            and self._motorPositionEqual(rowphase3, 0.0)
        ):
            # Negative Linear Arbitrary
            polarisation = "la"
            phase = rowphase2
            return polarisation, phase
        # UNKNOWN default to LH

        polarisation = None
        phase = 0.0
        return (polarisation, phase)


class I10Apple2PGM(StandardReadable, Movable):
    def __init__(self, id: I10Apple2, pgm: PGM, name: str = "") -> None:
        with self.add_children_as_readables():
            self.id = id
            self.pgm = pgm
        with self.add_children_as_readables(HintedSignal):
            self.energy_offset = soft_signal_rw(float, initial_value=0)
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        await asyncio.gather(
            self.id.set(value=value + await self.energy_offset.get_value()),
            self.pgm.energy.set(value),
        )


class I10Apple2Pol(StandardReadable, Movable):
    def __init__(self, id: I10Apple2, name: str = "") -> None:
        with self.add_children_as_readables():
            self.id = id
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: str) -> None:
        self.id.pol = value  # change polarisation.
        self.id.set(await self.id.energy.get_value())  # Move id to new polarisation


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
        # calculate polynomial energy to gap/phase
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
