import asyncio
from pathlib import Path

import numpy as np
import pandas as pd
from bluesky.protocols import Movable
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    wait_for_value,
)

from dodal.devices.apple2_undulator import (
    Apple2PhasesPv,
    Apple2Val,
    UndlatorPhaseAxes,
    UndulatorGap,
    UndulatorGatestatus,
)


class I10Apple2(StandardReadable, Movable):
    """
    Apple2 id with both phase and gap motion for i10.
    A pair of look up tables are needed to provide the conversion between motor position and energy.
    Set is in energy in eV.
    """

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
        self.lookup_tables = {}
        self.update_poly()
        self._available_pol = list(self.lookup_tables["Gap"].keys())
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
            lookup_table=self.lookup_tables["Gap"], new_energy=new_energy
        )
        phase_poly = self._get_poly(
            lookup_table=self.lookup_tables["Phase"], new_energy=new_energy
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

    def update_poly(self):
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
