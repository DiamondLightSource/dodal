import asyncio

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


def _get_energy_distance_table(lookup_table_path: str) -> ndarray:
    # TODO: Make IO async
    return loadtxt(lookup_table_path, comments=["#", "Units"])


def _get_closest_gap_for_energy(
    dcm_energy_ev: float, energy_to_distance_table: ndarray
) -> float:
    table = energy_to_distance_table.transpose()
    idx = argmin(np.abs(table[0] - dcm_energy_ev))
    return table[1][idx]


class UndulatorDCM(StandardReadable, Movable):
    """
    Composite device to handle changing beamline energies
    """

    _setpoint: float

    def __init__(self, undulator: Undulator, dcm: DCM, name: str = ""):
        self.undulator = undulator
        self.dcm = dcm

        super().__init__(name)

    def set(self, value: float) -> AsyncStatus:
        async def _set(value: float):
            # TODO: Break up into smaller methods
            energy_kev = value
            access_level = await self.undulator.gap_access.get_value()
            if access_level is UndulatorGapAccess.DISABLED and not TEST_MODE:
                raise AccessError(
                    "Undulator gap access is disabled. Contact Control Room"
                )

            # Get 2d np.array converting energies to undulator gap distance, from lookup table
            energy_to_distance_table = _get_energy_distance_table(
                self.undulator.lookup_table_path
            )
            LOGGER.info(f"Setting DCM energy to {energy_kev:.2f} kev")

            statuses = [
                self.dcm.energy_in_kev.set(
                    energy_kev,
                    timeout=ENERGY_TIMEOUT_S,
                )
            ]

            # Use the lookup table to get the undulator gap associated with this dcm energy
            gap_to_match_dcm_energy = _get_closest_gap_for_energy(
                energy_kev * 1000,
                energy_to_distance_table,
            )

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
                    statuses.append(
                        self.undulator.gap_motor.set(
                            gap_to_match_dcm_energy,
                            timeout=STATUS_TIMEOUT_S,
                        )
                    )
            await asyncio.gather(*statuses)

        return AsyncStatus(_set(value))
