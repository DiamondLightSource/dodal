import numpy as np

from dodal.devices.undulator import UndulatorInKeV, UndulatorOrder
from dodal.devices.util.lookup_tables import energy_distance_table


class InsertionDevice(UndulatorInKeV):
    """
    Insertion device for i07 including beamline-specific energy-gap lookup behaviour
    """

    def __init__(
        self,
        name: str,
        prefix: str,
        harmonic: UndulatorOrder,
        id_gap_lookup_table_path: str = "/dls_sw/i07/software/gda/config/lookupTables/"
        + "IIDCalibrationTable.txt",
    ) -> None:
        super().__init__(prefix, id_gap_lookup_table_path, name=name)
        self.harmonic = harmonic

    async def _get_gap_to_match_energy(self, energy_kev: float) -> float:
        """
        i07's energy scans remain on a particular harmonic while changing energy.  The
        calibration table has one row for each harmonic, row contains max and min
        energies and their corresponding ID gaps.  The requested energy is used to
        interpolate between these values, assuming a linear relationship on the relevant
        scale.
        """
        energy_to_distance_table: np.ndarray = await energy_distance_table(
            self.id_gap_lookup_table_path, comments="#", skiprows=2
        )
        harmonic_value: int = await self.harmonic.value.get_value()

        row: np.ndarray = energy_to_distance_table[harmonic_value - 1, :]
        gap = np.interp(energy_kev, [row[1], row[2]], [row[3], row[4]])
        return gap
