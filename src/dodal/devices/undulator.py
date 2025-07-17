import os

import numpy as np
from bluesky.protocols import Movable
from numpy import ndarray
from ophyd_async.core import (
    AsyncStatus,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.epics.motor import Motor

from dodal.log import LOGGER

from .util.lookup_tables import energy_distance_table


class AccessError(Exception):
    pass


# Enable to allow testing when the beamline is down, do not change in production!
TEST_MODE = False
# will be made more generic in https://github.com/DiamondLightSource/dodal/issues/754


# The acceptable difference, in mm, between the undulator gap and the DCM
# energy, when the latter is converted to mm using lookup tables
UNDULATOR_DISCREPANCY_THRESHOLD_MM = 2e-3
STATUS_TIMEOUT_S: float = 10.0


class UndulatorGapAccess(StrictEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


def _get_gap_for_energy(
    dcm_energy_ev: float, energy_to_distance_table: ndarray
) -> float:
    return np.interp(
        dcm_energy_ev, energy_to_distance_table[:, 0], energy_to_distance_table[:, 1]
    )


class Undulator(StandardReadable, Movable[float]):
    """
    An Undulator-type insertion device, used to control photon emission at a given
    beam energy.
    """

    def __init__(
        self,
        prefix: str,
        id_gap_lookup_table_path: str = os.devnull,
        name: str = "",
        poles: int | None = None,
        length: float | None = None,
    ) -> None:
        """Constructor

        Args:
            prefix: PV prefix
            poles (int): Number of magnetic poles built into the undulator
            length (float): Length of the undulator in meters
            name (str, optional): Name for device. Defaults to "".
        """

        self.id_gap_lookup_table_path = id_gap_lookup_table_path
        with self.add_children_as_readables():
            self.gap_motor = Motor(prefix + "BLGAPMTR")
            self.current_gap = epics_signal_r(float, prefix + "CURRGAPD")
            self.gap_access = epics_signal_r(UndulatorGapAccess, prefix + "IDBLENA")

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.gap_discrepancy_tolerance_mm, _ = soft_signal_r_and_setter(
                float,
                initial_value=UNDULATOR_DISCREPANCY_THRESHOLD_MM,
            )
            if poles is not None:
                self.poles, _ = soft_signal_r_and_setter(
                    int,
                    initial_value=poles,
                )
            else:
                self.poles = None

            if length is not None:
                self.length, _ = soft_signal_r_and_setter(
                    float,
                    initial_value=length,
                )
            else:
                self.length = None

        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        """
        Set the undulator gap to a given energy in keV

        Args:
            value: energy in keV
        """
        await self._set_undulator_gap(value)

    async def raise_if_not_enabled(self):
        access_level = await self.gap_access.get_value()
        if access_level is UndulatorGapAccess.DISABLED and not TEST_MODE:
            raise AccessError("Undulator gap access is disabled. Contact Control Room")

    async def _set_undulator_gap(self, energy_kev: float) -> None:
        await self.raise_if_not_enabled()
        target_gap = await self._get_gap_to_match_energy(energy_kev)
        LOGGER.info(
            f"Setting undulator gap to {target_gap:.3f}mm based on {energy_kev:.2f}kev"
        )

        # Check if undulator gap is close enough to the value from the DCM
        current_gap = await self.current_gap.get_value()
        tolerance = await self.gap_discrepancy_tolerance_mm.get_value()
        difference = abs(target_gap - current_gap)
        if difference > tolerance:
            LOGGER.info(
                f"Undulator gap mismatch. {difference:.3f}mm is outside tolerance.\
                Moving gap to nominal value, {target_gap:.3f}mm"
            )
            if not TEST_MODE:
                # Only move if the gap is sufficiently different to the value from the
                # DCM lookup table AND we're not in TEST_MODE
                await self.gap_motor.set(
                    target_gap,
                    timeout=STATUS_TIMEOUT_S,
                )
            else:
                LOGGER.debug("In test mode, not moving ID gap")
        else:
            LOGGER.debug(
                "Gap is already in the correct place for the new energy value "
                f"{energy_kev}, no need to ask it to move"
            )

    async def _get_gap_to_match_energy(self, energy_kev: float) -> float:
        """
        get a 2d np.array from lookup table that
        converts energies to undulator gap distance
        """
        energy_to_distance_table: np.ndarray = await energy_distance_table(
            self.id_gap_lookup_table_path
        )

        # Use the lookup table to get the undulator gap associated with this dcm energy
        return _get_gap_for_energy(
            energy_kev * 1000,
            energy_to_distance_table,
        )
