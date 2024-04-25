import asyncio
from io import StringIO

import aiofiles
import numpy as np
from bluesky.protocols import Movable
from numpy import argmin, loadtxt, ndarray
from ophyd_async.core import AsyncStatus, StandardReadable

from dodal.devices.dcm import DCM
from dodal.devices.undulator import Undulator, UndulatorGapAccess
from dodal.log import LOGGER

ENERGY_TIMEOUT_S: float = 30.0
STATUS_TIMEOUT_S: float = 10.0

# Enable to allow testing when the beamline is down, do not change in production!
TEST_MODE = False


class AccessError(Exception):
    pass


async def _get_energy_distance_table(lookup_table_path: str) -> ndarray:
    # Slight cheat to make the file IO async, numpy doesn't do any real IO now, just
    # decodes the text
    async with aiofiles.open(lookup_table_path, "r") as stream:
        raw_table = await stream.read()
    return loadtxt(StringIO(raw_table), comments=["#", "Units"])


def _get_closest_gap_for_energy(
    dcm_energy_ev: float, energy_to_distance_table: ndarray
) -> float:
    table = energy_to_distance_table.transpose()
    idx = argmin(np.abs(table[0] - dcm_energy_ev))
    return table[1][idx]


class UndulatorDCM(StandardReadable, Movable):
    """
    Composite device to handle changing beamline energies, wraps the Undulator and the
    DCM. The DCM has a motor which controls the beam energy, when it moves, the
    Undulator gap may also have to change to enable emission at the new energy.
    The relationship between the two motor motor positions is provided via a lookup
    table.

    Calling unulator_dcm.set(energy) will move the DCM motor, perform a table lookup
    and move the Undulator gap motor if needed. So the set method can be thought of as
    a comprehensive way to set beam energy.
    """

    def __init__(
        self,
        undulator: Undulator,
        dcm: DCM,
        prefix: str = "",
        name: str = "",
    ):
        super().__init__(name)

        # Attributes are set after super call so they are not renamed to
        # <name>-undulator, etc.
        self.undulator = undulator
        self.dcm = dcm

    def set(self, value: float) -> AsyncStatus:
        async def _set():
            await asyncio.gather(
                self._set_dcm_energy(value),
                self._set_undulator_gap_if_required(value),
            )

        return AsyncStatus(_set())

    async def _set_dcm_energy(self, energy_kev: float) -> None:
        access_level = await self.undulator.gap_access.get_value()
        if access_level is UndulatorGapAccess.DISABLED and not TEST_MODE:
            raise AccessError("Undulator gap access is disabled. Contact Control Room")

        await self.dcm.energy_in_kev.set(
            energy_kev,
            timeout=ENERGY_TIMEOUT_S,
        )

    async def _set_undulator_gap_if_required(self, energy_kev: float) -> None:
        LOGGER.info(f"Setting DCM energy to {energy_kev:.2f} kev")
        gap_to_match_dcm_energy = await self._gap_to_match_dcm_energy(energy_kev)

        # Check if undulator gap is close enough to the value from the DCM
        current_gap = await self.undulator.current_gap.get_value()
        if (
            abs(gap_to_match_dcm_energy - current_gap)
            > self.undulator.gap_discrepancy_tolerance_mm
        ):
            LOGGER.info(
                f"Undulator gap mismatch. {abs(gap_to_match_dcm_energy-current_gap):.3f}mm is outside tolerance.\
                Moving gap to nominal value, {gap_to_match_dcm_energy:.3f}mm"
            )
            if not TEST_MODE:
                # Only move if the gap is sufficiently different to the value from the
                # DCM lookup table AND we're not in TEST_MODE
                await self.undulator.gap_motor.set(
                    gap_to_match_dcm_energy,
                    timeout=STATUS_TIMEOUT_S,
                )
            else:
                LOGGER.debug("In test mode, not moving ID gap")
        else:
            LOGGER.debug(
                "Gap is already in the correct place for the new energy value "
                f"{energy_kev}, no need to ask it to move"
            )

    async def _gap_to_match_dcm_energy(self, energy_kev: float) -> float:
        # Get 2d np.array converting energies to undulator gap distance, from lookup table
        energy_to_distance_table = await _get_energy_distance_table(
            self.undulator.lookup_table_path
        )

        # Use the lookup table to get the undulator gap associated with this dcm energy
        return _get_closest_gap_for_energy(
            energy_kev * 1000,
            energy_to_distance_table,
        )
