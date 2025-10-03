import os

import numpy as np
from bluesky.protocols import Movable
from numpy import ndarray
from ophyd_async.core import (
    AsyncStatus,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    soft_signal_r_and_setter,
)
from ophyd_async.epics.core import epics_signal_r
from ophyd_async.epics.motor import Motor

from dodal.common.enums import EnabledDisabledUpper
from dodal.log import LOGGER

from .baton import Baton
from .util.lookup_tables import energy_distance_table


class AccessError(Exception):
    pass


# The acceptable difference, in mm, between the undulator gap and the DCM
# energy, when the latter is converted to mm using lookup tables
UNDULATOR_DISCREPANCY_THRESHOLD_MM = 2e-3
STATUS_TIMEOUT_S: float = 10.0


def _get_gap_for_energy(
    dcm_energy_ev: float, energy_to_distance_table: ndarray
) -> float:
    return np.interp(
        dcm_energy_ev, energy_to_distance_table[:, 0], energy_to_distance_table[:, 1]
    )


class UndulatorBase(StandardReadable):
    """
    Base class for undulator devices providing gap control and access management.

        prefix (str): EPICS PV prefix for the undulator device.
        baton (Baton | None, optional): Reference to a Baton object for commissioning mode checks.
        name (str, optional): Name of the device.
    """

    def __init__(
        self,
        prefix: str,
        baton: Baton | None = None,
        name: str = "",
    ) -> None:
        """
        Args:
            prefix: PV prefix
            baton: baton object if provided.
            name: Name for device. Defaults to ""
        """
        self.baton_ref = Reference(baton) if baton else None

        with self.add_children_as_readables():
            self.gap_access = epics_signal_r(EnabledDisabledUpper, prefix + "IDBLENA")
            self.gap_motor = Motor(prefix + "BLGAPMTR")
            self.current_gap = epics_signal_r(float, prefix + "CURRGAPD")

        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.gap_discrepancy_tolerance_mm, _ = soft_signal_r_and_setter(
                float,
                initial_value=UNDULATOR_DISCREPANCY_THRESHOLD_MM,
            )
        super().__init__(name=name)

    async def check_gap_within_threshold(self, target_gap: float) -> bool:
        """
        Check if the undulator gap is within the acceptable threshold of the target gap

        Args:
            target_gap: target gap in mm
        Returns:
            True if the gap is within the threshold, False otherwise
        """
        current_gap = await self.current_gap.get_value()
        tolerance = await self.gap_discrepancy_tolerance_mm.get_value()
        return abs(target_gap - current_gap) <= tolerance

    async def _is_commissioning_mode_enabled(self) -> bool | None:
        """
        Asynchronously checks if commissioning mode is enabled via the baton reference.
        """
        return self.baton_ref and await self.baton_ref().commissioning.get_value()

    async def raise_if_not_enabled(self) -> AccessError | None:
        """
        Asynchronously raises AccessError if gap access is disabled and not in commissioning mode.
        """
        access_level = await self.gap_access.get_value()
        commissioning_mode = await self._is_commissioning_mode_enabled()
        if access_level is EnabledDisabledUpper.DISABLED and not commissioning_mode:
            raise AccessError("Undulator gap access is disabled. Contact Control Room")


class Undulator(UndulatorBase, Movable[float]):
    """
    An Undulator-type insertion device, used to control photon emission at a given
    beam energy.
    """

    def __init__(
        self,
        prefix: str,
        id_gap_lookup_table_path: str = os.devnull,
        poles: int | None = None,
        length: float | None = None,
        baton: Baton | None = None,
        name: str = "",
    ) -> None:
        """Constructor

        Args:
            prefix: PV prefix
            poles (int): Number of magnetic poles built into the undulator
            length (float): Length of the undulator in meters
            name (str, optional): Name for device. Defaults to "".
        """

        self.id_gap_lookup_table_path = id_gap_lookup_table_path
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
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

        super().__init__(prefix=prefix, baton=baton, name=name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        """
        Check conditions and Set undulator gap to a given energy in keV

        Args:
            value: energy in keV
        """
        await self.raise_if_not_enabled()  # Check access
        target_gap = await self._get_gap_to_match_energy(value)
        LOGGER.info(
            f"Setting undulator gap to {target_gap:.3f}mm based on {value:.2f}kev"
        )
        if await self.check_gap_within_threshold(target_gap):
            LOGGER.debug(
                "Gap is already in the correct place for the new energy value "
                f"{value}, no need to ask it to move"
            )
            return

        await self._set_undulator_gap(target_gap)

    async def _set_undulator_gap(self, target_gap: float) -> None:
        """
        Set the undulator gap to a given value in mm

        Args:
            value: gap in mm
        """
        LOGGER.info(
            f"Undulator gap mismatch. Moving gap to nominal value, {target_gap:.3f}mm"
        )
        commissioning_mode = await self._is_commissioning_mode_enabled()
        if not commissioning_mode:
            # Only move if the gap is sufficiently different to the value from the
            # DCM lookup table AND we're not in commissioning mode
            await self.gap_motor.set(
                target_gap,
                timeout=STATUS_TIMEOUT_S,
            )
        else:
            LOGGER.warning("In test mode, not moving ID gap")

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
