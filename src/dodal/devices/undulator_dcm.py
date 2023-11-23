import numpy as np
from numpy import argmin, loadtxt, ndarray
from ophyd import Component, Device, EpicsMotor, EpicsSignalRO, Signal
from ophyd.status import Status

from dodal.devices.DCM import DCM
from dodal.devices.undulator import Undulator, UndulatorGapAccess
from dodal.log import LOGGER


class AccessError(Exception):
    pass


def _get_closest_gap_to_dcm_energy(
    dcm_energy: float, energy_to_distance_table: ndarray
) -> float:
    idx = argmin(np.abs(energy_to_distance_table[0] - dcm_energy))
    return energy_to_distance_table[1][idx]


# def _get_energy_to_distance_table(lookup_table_path: str) -> dict[float, float]:
#     energy_to_distance_table: dict[float, float] = {}
#     with open(lookup_table_path, mode="r") as table:
#         table_start = False
#         for line in table:
#             line = line.strip()
#             if line.startswith("Units"):
#                 table_start = True
#                 continue
#             if table_start:
#                 value = line.split()
#                 energy_to_distance_table[float(value[0])] = float(value[1])
#     return energy_to_distance_table


# Composite device to handle changing beamline energies
class UndulatorDCM(Device):
    class EnergySignal(Signal):
        def set(self, value, *, timeout=None, settle_time=None, **kwargs) -> Status:
            access_level = self.parent.undulator.gap_access.get()
            if access_level == UndulatorGapAccess.DISABLED.value:
                LOGGER.error("Undulator gap access is disabled. Contact Control Room")
                raise AccessError(
                    "Undulator gap access is disabled. Contact Control Room"
                )

            # Get dict converting energies to undulator gap distance, from lookup table
            energy_to_distance_table = loadtxt(
                self.parent.undulator.lookup_table_path, comments="Units"
            )

            dcm_energy = self.parent.dcm.energy_in_kev.user_readback.get()
            self.parent.dcm.energy_in_kev.


            # Use the lookup table to get the undulator gap associated with this dcm energy
            gap_to_match_dcm_energy = _get_closest_gap_to_dcm_energy(
                dcm_energy, energy_to_distance_table
            )

            # Check if undulator gap is close enough to the value from the DCM
            current_gap = self.parent.undulator.current_gap.get()

            if (
                abs(gap_to_match_dcm_energy - current_gap)
                > self.parent.undulator.gap_discrepancy_tolerance_mm
            ):
                LOGGER.info(
                    f"Undulator gap mismatch. {abs(gap_to_match_dcm_energy-current_gap):.3f} is outside tolerance.\
                    Restoring gap to nominal value, {gap_to_match_dcm_energy}"
                )
                return self.parent.undulator.gap_motor.set(gap_to_match_dcm_energy)

            complete_status = Status()
            complete_status.set_finished()
            return complete_status

    energy: EnergySignal = Component(EnergySignal)

    def __init__(self, undulator: Undulator, dcm: DCM, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.undulator = undulator
        self.dcm = dcm
