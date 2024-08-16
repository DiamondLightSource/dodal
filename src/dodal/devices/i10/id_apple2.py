import asyncio
import csv
import warnings
from pathlib import Path

import numpy as np
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
        poly_deg: list | None = None,
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
    poly_deg: list | None = None,
):
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
    with open(
        "/workspaces/dodal/tests/devices/i10/lookupTables/IDEnergy2GapCalibrations.csv",
        newline="",
    ) as csvfile:
        reader = csv.DictReader(csvfile)
        reader = sorted(reader, key=lambda d: float(d[min_energy]))
        for row in reader:
            if source is not None:
                # If there are multiple source only do one
                if row[source[0]] == source[1]:
                    if row[mode] not in pol:
                        pol.append(row[mode])
                        look_up_table[row[mode]] = {}
                        look_up_table[row[mode]]["Energies"] = {}
                        look_up_table[row[mode]]["Limit"] = {}
                        look_up_table[row[mode]]["Limit"]["Minimum"] = float(
                            row[min_energy]
                        )
                        look_up_table[row[mode]]["Limit"]["Maximum"] = float(
                            row[max_energy]
                        )
                    # calculate polynomial energy to gap/phase
                    cof = [float(row[x]) for x in poly_deg]
                    poly = np.poly1d(cof)
                    energy_range = np.arange(
                        float(row[min_energy]), float(row[max_energy]), 0.5
                    )
                    y = poly(energy_range)
                    # calculate polynomial gap/phase to energy
                    with warnings.catch_warnings():  # the fitting warning can be ignored as we checking the fit later
                        warnings.filterwarnings(
                            "ignore", "Polyfit may be poorly conditioned"
                        )
                        inverse_poly = np.poly1d(
                            np.polyfit(x=y, y=energy_range, deg=len(cof))
                        )
                    inverse_y = inverse_poly(y)
                    # check fit
                    np.testing.assert_almost_equal(energy_range, inverse_y, 0)
                    look_up_table[row[mode]]["Energies"][row[min_energy]] = {
                        "Low": float(row[min_energy]),
                        "High": float(row[max_energy]),
                        "Poly": poly,
                        "Inverse poly": inverse_poly,
                    }
                    if look_up_table[row[mode]]["Limit"]["Minimum"] > float(
                        row[min_energy]
                    ):
                        look_up_table[row[mode]]["Limit"]["Minimum"] = float(
                            row[min_energy]
                        )
                    if look_up_table[row[mode]]["Limit"]["Maximum"] < float(
                        row[min_energy]
                    ):
                        look_up_table[row[mode]]["Limit"]["Maximum"] = float(
                            row[max_energy]
                        )
    return look_up_table
