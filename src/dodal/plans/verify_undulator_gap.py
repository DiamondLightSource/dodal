from dodal.devices.DCM import DCM
from dodal.devices.undulator import Undulator, UndulatorGapAccess
from dodal.log import LOGGER


def verify_undulator_gap(
    undulator: Undulator, DCM: DCM, lookup_table_path: str
) -> bool:
    """This function should:
    Check access level
    Read the current beam energy from the DCM:
    Convert this to a distance using the lookup table
    Read the current undulator gap
    Check the DCM distance is within tolerated distance to undulator gap

    """

    access_level = undulator.gap_access.get()
    if access_level == UndulatorGapAccess.DISABLED.value:
        LOGGER.warning(
            "Undulator gap access is disabled. Unable to verify undulator gap"
        )
        return False

    # Get dict converting energies to undulator gap distance, from lookup table
    energy_to_distance_table: dict[float, float] = {}
    with open(undulator.lookup_table_path) as table:
        table_start = False
        for line in table:
            if line.startswith("Units"):
                table_start = True
            if table_start:
                value = line.split()
                energy_to_distance_table[float(value[0])] = float(value[1])

    # Convert energy fom dcm to undulator gap distance
    dcm_energy = DCM.energy_in_kev.get()
    table_energies = energy_to_distance_table.keys()
    table_energy_value_to_use: float = 0
    closest_distance_to_energy_from_table = dcm_energy
    for energy in table_energies:
        distance = abs(dcm_energy - energy)
        if distance < closest_distance_to_energy_from_table:
            closest_distance_to_energy_from_table = distance
            table_energy_value_to_use = energy
    gap_to_match_dcm_energy = energy_to_distance_table[table_energy_value_to_use]

    # Check if undulator gap is close enough to the value from the DCM
    current_gap = undulator.gap.get()
    if abs(gap_to_match_dcm_energy - current_gap) > undulator.gap_discrepancy_tolerance:
        LOGGER.warning(
            f"Undulator gap mismatch. f{abs(gap_to_match_dcm_energy-current_gap)} is outside tolerance.\
            Restoring gap to nominal value, f{gap_to_match_dcm_energy}"
        )
        undulator.gap.set(gap_to_match_dcm_energy).wait(10)

    return True
