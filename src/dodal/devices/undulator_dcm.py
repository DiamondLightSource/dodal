import numpy as np
from numpy import argmin, loadtxt, ndarray
from ophyd import Component, Device, Signal
from ophyd.status import Status

from dodal.devices.DCM import DCM
from dodal.devices.undulator import Undulator, UndulatorGapAccess
from dodal.log import LOGGER

STATUS_TIMEOUT = 10


class AccessError(Exception):
    pass


def _get_energy_distance_table(lookup_table_path: str) -> ndarray:
    return loadtxt(lookup_table_path, comments=["#", "Units"])


def _get_closest_gap_for_energy(
    dcm_energy: float, energy_to_distance_table: ndarray
) -> float:
    table = energy_to_distance_table.transpose()
    idx = argmin(np.abs(table[0] - dcm_energy))
    return table[1][idx]


class UndulatorDCM(Device):
    """
    Composite device to handle changing beamline energies
    """

    class EnergySignal(Signal):
        parent: "UndulatorDCM"

        def set(self, value, *, timeout=None, settle_time=None, **kwargs) -> Status:
            access_level = self.parent.undulator.gap_access.get()
            if access_level == UndulatorGapAccess.DISABLED.value:
                raise AccessError(
                    "Undulator gap access is disabled. Contact Control Room"
                )

            # Get 2d np.array converting energies to undulator gap distance, from lookup table
            energy_to_distance_table = _get_energy_distance_table(
                self.parent.undulator.lookup_table_path
            )
            LOGGER.info(f"Setting DCM energy to {value:.2f} kev")

            status = self.parent.dcm.energy_in_kev.move(value, timeout=STATUS_TIMEOUT)

            # Use the lookup table to get the undulator gap associated with this dcm energy
            gap_to_match_dcm_energy = _get_closest_gap_for_energy(
                value, energy_to_distance_table
            )

            # Check if undulator gap is close enough to the value from the DCM
            current_gap = self.parent.undulator.current_gap.get()

            if (
                abs(gap_to_match_dcm_energy - current_gap)
                > self.parent.undulator.gap_discrepancy_tolerance_mm
            ):
                LOGGER.info(
                    f"Undulator gap mismatch. {abs(gap_to_match_dcm_energy-current_gap):.3f}mm is outside tolerance.\
                    Moving gap to nominal value, {gap_to_match_dcm_energy:.3f}mm"
                )
                status &= self.parent.undulator.gap_motor.move(
                    gap_to_match_dcm_energy, timeout=STATUS_TIMEOUT
                )

            return status

    energy_kev = Component(EnergySignal)

    def __init__(self, undulator: Undulator, dcm: DCM, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.undulator = undulator
        self.dcm = dcm
