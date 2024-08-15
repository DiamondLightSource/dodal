import asyncio
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import numpy as np
import pandas as pd
from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    ConfigSignal,
    HintedSignal,
    StandardReadable,
    wait_for_value,
)
from ophyd_async.epics.signal import epics_signal_r, epics_signal_rw, epics_signal_w


class UndulatorGatestatus(str, Enum):
    open = "Open"
    close = "Closed"


@dataclass
class Apple2PhasesVal:
    top_outer: str
    top_inner: str
    btm_outer: str
    btm_inner: str


@dataclass
class Apple2PhasesPv:
    top_outer: str
    top_inner: str
    btm_outer: str
    btm_inner: str


@dataclass
class Apple2Val:
    gap: str
    top_outer: str
    top_inner: str
    btm_outer: str
    btm_inner: str


class UndulatorGap(StandardReadable, Movable):
    """A device with a collection of epics signals to set Apple 2 undulator gap motion.
    Only PV used by beamline are added the full list is here:
    /dls_sw/work/R3.14.12.7/support/insertionDevice/db/IDGapVelocityControl.template
    /dls_sw/work/R3.14.12.7/support/insertionDevice/db/IDPhaseSoftMotor.template
    """

    def __init__(self, prefix: str, name: str = ""):
        """
        Constructs all the necessary PV for the pundulatorGap.

        Parameters
        ----------
            prefix : str
                Beamline specific part of the PV
            name : str
                Name of the Id device

        """

        # Gap demand set point and readback
        self.user_setpoint = epics_signal_rw(
            str, prefix + "GAPSET.B", prefix + "BLGSET"
        )
        # Nothing move until this is set to 1 and it will return to 0 when done
        self.set_move = epics_signal_rw(int, prefix + "BLGSETP")
        # Gate keeper open when move is requested, closed when move is completed
        self.gate = epics_signal_r(UndulatorGatestatus, prefix + "BLGATE")
        # These are gap velocity limit.
        self.max_velocity = epics_signal_r(float, prefix + "BLGSETVEL.HOPR")
        self.min_velocity = epics_signal_r(float, prefix + "BLGSETVEL.LOPR")
        # These are gap limit.
        self.high_limit = epics_signal_r(float, prefix + "BLGAPMTR.HLM")
        self.low_limit = epics_signal_r(float, prefix + "BLGAPMTR.LLM")

        # This is calculated acceleration from speed
        self.acceleration_time = epics_signal_r(float, prefix + "IDGSETACC")
        with self.add_children_as_readables(ConfigSignal):
            # Unit
            self.motor_egu = epics_signal_r(str, prefix + "BLGAPMTR.EGU")
            # Gap velocity
            self.velocity = epics_signal_rw(float, prefix + "BLGSETVEL")
        with self.add_children_as_readables(HintedSignal):
            # Gap readback value
            self.user_readback = epics_signal_r(float, prefix + "CURRGAPD")
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value) -> None:
        if await self.gate.get_value() == UndulatorGatestatus.open:
            raise RuntimeError(f"{self.name} is already in motion.")
        await self.user_setpoint.set(value=str(value))
        timeout = await self._cal_timeout()
        await self.set_move.set(value=1)
        await wait_for_value(self.gate, UndulatorGatestatus.close, timeout=timeout)

    async def _cal_timeout(self) -> float:
        vel = await self.velocity.get_value()
        cur_pos = await self.user_readback.get_value()
        target_pos = float(await self.user_setpoint.get_value())
        return abs((target_pos - cur_pos) * 2.0 / vel)

    async def get_timeout(self) -> float:
        return await self._cal_timeout()


class UndulatorPhaseMotor(StandardReadable):
    """A collection of epics signals for ID phase motion.
    Only PV used by beamline are added the full list is here:
    /dls_sw/work/R3.14.12.7/support/insertionDevice/db/IDPhaseSoftMotor.template


    """

    def __init__(self, prefix: str, infix: str, name: str = ""):
        """
        Parameters
        ----------

        prefix : str
            The setting prefix PV.
        infix: str
            Collection of pv that are different between beamlines
        name : str
            Name of the Id phase device
        """
        fullPV = prefix + "BL" + infix + "MTR"
        self.user_setpoint = epics_signal_w(str, fullPV[:-3] + "SET")
        self.user_setpoint_demand_readback = epics_signal_r(float, fullPV[:-3] + "DMD")
        with self.add_children_as_readables(HintedSignal):
            self.user_setpoint_readback = epics_signal_r(float, fullPV + ".RBV")

        with self.add_children_as_readables(ConfigSignal):
            self.motor_egu = epics_signal_r(str, fullPV + ".EGU")
            self.velocity = epics_signal_rw(float, fullPV + ".VELO")

            self.max_velocity = epics_signal_r(float, fullPV + ".VMAX")
            self.acceleration_time = epics_signal_rw(float, fullPV + ".ACCL")
            self.precision = epics_signal_r(int, fullPV + ".PREC")
            self.deadband = epics_signal_r(float, fullPV + ".RDBD")
            self.motor_done_move = epics_signal_r(int, fullPV + ".DMOV")
            self.low_limit_travel = epics_signal_rw(float, fullPV + ".LLM")
            self.high_limit_travel = epics_signal_rw(float, fullPV + ".HLM")

        super().__init__(name=name)


class UndlatorPhaseAxes(StandardReadable, Movable):
    """A collection of 4 phase Motor to make up"""

    def __init__(
        self,
        prefix: str,
        top_outer: str,
        top_inner: str,
        btm_outer: str,
        btm_inner: str,
        name: str = "",
    ):
        # Gap demand set point and readback
        with self.add_children_as_readables():
            self.top_outer = UndulatorPhaseMotor(prefix=prefix, infix=top_outer)
            self.top_inner = UndulatorPhaseMotor(prefix=prefix, infix=top_inner)
            self.btm_outer = UndulatorPhaseMotor(prefix=prefix, infix=btm_outer)
            self.btm_inner = UndulatorPhaseMotor(prefix=prefix, infix=btm_inner)
        # Nothing move until this is set to 1 and it will return to 0 when done
        self.set_move = epics_signal_rw(int, prefix + "BLGSETP")
        self.gate = epics_signal_r(UndulatorGatestatus, prefix + "BLGATE")
        super().__init__(name=name)

    @AsyncStatus.wrap
    async def set(self, value: Apple2PhasesVal) -> None:
        if await self.gate.get_value() == UndulatorGatestatus.open:
            raise RuntimeError(f"{self.name} is already in motion.")
        await asyncio.gather(
            self.top_outer.user_setpoint.set(value=value.top_outer),
            self.top_inner.user_setpoint.set(value=value.top_inner),
            self.btm_outer.user_setpoint.set(value=value.btm_outer),
            self.btm_inner.user_setpoint.set(value=value.btm_inner),
        )
        timeout = await self._cal_timeout()
        await self.set_move.set(value=1)
        await wait_for_value(self.gate, UndulatorGatestatus.close, timeout=timeout)

    async def _cal_timeout(self) -> float:
        velos = await asyncio.gather(
            self.top_outer.velocity.get_value(),
            self.top_inner.velocity.get_value(),
            self.btm_outer.velocity.get_value(),
            self.btm_inner.velocity.get_value(),
        )
        cur_pos = await asyncio.gather(
            self.top_outer.user_setpoint_demand_readback.get_value(),
            self.top_inner.user_setpoint_demand_readback.get_value(),
            self.btm_outer.user_setpoint_demand_readback.get_value(),
            self.btm_inner.user_setpoint_demand_readback.get_value(),
        )
        target_pos = await asyncio.gather(
            self.top_outer.user_setpoint_readback.get_value(),
            self.top_inner.user_setpoint_readback.get_value(),
            self.btm_outer.user_setpoint_readback.get_value(),
            self.btm_inner.user_setpoint_readback.get_value(),
        )
        move_time = np.abs(np.divide(tuple(np.subtract(target_pos, cur_pos)), velos))

        return move_time.max() * 2

    async def get_timeout(self) -> float:
        return await self._cal_timeout()


class Apple2Undlator(StandardReadable, Movable):
    def __init__(
        self,
        prefix: str,
        infix: Apple2PhasesPv,
        energy_gap_table_path: Path,
        energy_phase_table_path: Path,
        source: tuple[str, str] | None = None,
        mode: str = "Mode",
        min_energy: str = "MinEnergy",
        max_energy: str = "MaxEnergy",
        poly_deg: int = 8,
        name: str = "",
    ) -> None:
        with self.add_children_as_readables():
            self.gap = UndulatorGap(prefix=prefix)
            self.phase = UndlatorPhaseAxes(
                prefix=prefix,
                top_inner=infix.top_inner,
                top_outer=infix.top_outer,
                btm_inner=infix.btm_inner,
                btm_outer=infix.btm_outer,
            )
        super().__init__(name)
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
        self.lookup_table = {}
        self._update_poly()
        self._available_pol = list(self.lookup_table["Gap"].keys())
        self.detune = 0
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
    async def _set(self, value: Apple2Val) -> None:
        if await self.gap.gate.get_value() == UndulatorGatestatus.open:
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
        await self.gap.set_move.set(value=1)
        await wait_for_value(self.gap.gate, UndulatorGatestatus.close, timeout=timeout)

    @AsyncStatus.wrap
    async def set(self, value: float) -> None:
        gap, phase = self._get_id_gap_phase(value)
        id_set_val = Apple2Val(
            top_outer=str(phase),
            top_inner="0.0",
            btm_inner=str(-phase),
            btm_outer="0.0",
            gap=str(gap),
        )
        await self._set(value=id_set_val)

    def _get_id_gap_phase(self, energy) -> tuple[float, float]:
        """
        Converts energy and polarisation to  gap and phase.
        """
        new_energy = energy + self.detune
        gap_poly = self._get_poly(
            lookup_table=self.lookup_table["Gap"], new_energy=new_energy
        )
        phase_poly = self._get_poly(
            lookup_table=self.lookup_table["Phase"], new_energy=new_energy
        )
        return gap_poly(new_energy), phase_poly(new_energy)

    def _get_poly(self, new_energy, lookup_table) -> np.poly1d:
        print(lookup_table.keys())
        if (
            new_energy < lookup_table[self.pol]["Energy"]["Limits"]["Minimum"]
            or new_energy > lookup_table[self.pol]["Energy"]["Limits"]["Maximum"]
        ):
            raise ValueError(
                "Demanding energy must lie between {} and {} eV!".format(
                    lookup_table[self.pol]["Energy"]["Limits"]["Minimum"],
                    lookup_table[self.pol]["Energy"]["Limits"]["Maximum"],
                )
            )
        else:
            for energy_range in lookup_table[self.pol]["Energy"]["Energies"].values():
                if (
                    new_energy >= energy_range["Low"]
                    and new_energy < energy_range["High"]
                ):
                    return energy_range["Poly"]

        raise Exception(
            "Cannot find polynomial coefficients for your requested energy."
            + "There might be gap in the calibration lookup table."
        )

    def _update_poly(self):
        for key, path in self.lookup_table_config["path"].items():
            if path.exists():
                self.lookup_table[key] = convert_csv_to_lookup(
                    file=path,
                    source=self.lookup_table_config["source"],
                    mode=self.lookup_table_config["mode"],
                    min_energy=self.lookup_table_config["min_energy"],
                    max_energy=self.lookup_table_config["max_energy"],
                    poly_deg=self.lookup_table_config["poly_deg"],
                )
            else:
                raise FileNotFoundError(f"{key} look up table is not in path: {path}")


def convert_csv_to_lookup(
    file,
    source: tuple[str, str] | None = None,
    mode: str = "Mode",
    min_energy: str = "MinEnergy",
    max_energy: str = "MaxEnergy",
    poly_deg: int = 8,
):
    df = pd.read_csv(file)
    look_up_table = {}
    if source is not None:
        # If there are multipu source only do one
        df = df.loc[df[source[0]] == source[1]].drop(source[0], axis=1)
    id_modes = df[mode].unique()  # Get mode from the lookup table
    for i in id_modes:
        # work on one pol/mode at a time.
        temp_df = (
            df.loc[df[mode] == i]
            .drop(mode, axis=1)
            .sort_values(by=min_energy)
            .reset_index()
        )
        look_up_table[i] = {}
        look_up_table[i]["Energy"] = {}
        look_up_table[i]["Energy"]["Limits"] = {
            "Minimum": temp_df.iloc[0][min_energy],
            "Maximum": temp_df.iloc[-1][max_energy],
        }
        look_up_table[i]["Energy"]["Energies"] = {}
        for index, row in temp_df.iterrows():
            poly = np.poly1d(row.values[::-1][:poly_deg])

            look_up_table[i]["Energy"]["Energies"][index] = {
                "Low": row[min_energy],
                "High": row[max_energy],
                "Poly": poly,
            }

    return look_up_table
