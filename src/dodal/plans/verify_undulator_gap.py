from dodal.devices.DCM import DCM
from dodal.devices.undulator import Undulator, UndulatorGapAccess
from dodal.log import LOGGER


def _get_energy_to_distance_table(lookup_table_path: str) -> dict[float, float]:
    energy_to_distance_table: dict[float, float] = {}
    with open(lookup_table_path, mode="r") as table:
        table_start = False
        for line in table:
            line = line.strip()
            if line.startswith("Units"):
                table_start = True
                continue
            if table_start:
                value = line.split()
                energy_to_distance_table[float(value[0])] = float(value[1])
    return energy_to_distance_table


def _get_closest_gap_to_dcm_energy(
    dcm_energy: float, energy_to_distance_table: dict[float, float]
) -> float:
    table_energies = energy_to_distance_table.keys()
    table_energy_value_to_use: float = 0
    closest_distance_to_energy_from_table = dcm_energy
    for energy in table_energies:
        distance = abs(dcm_energy - energy)
        if distance < closest_distance_to_energy_from_table:
            closest_distance_to_energy_from_table = distance
            table_energy_value_to_use = energy
    return energy_to_distance_table[table_energy_value_to_use]


def verify_undulator_gap(undulator: Undulator, DCM: DCM) -> bool:
    """
    If undulator access level is enabled, check that the undulator gap matches the
    energy from the DCM. If it doesn't match, set the undulator gap.
    """

    access_level = undulator.gap_access.get()
    if access_level == UndulatorGapAccess.DISABLED.value:
        LOGGER.warning(
            "Undulator gap access is disabled. Unable to verify undulator gap"
        )
        return False

    # Get dict converting energies to undulator gap distance, from lookup table
    energy_to_distance_table = _get_energy_to_distance_table(
        undulator.lookup_table_path
    )

    dcm_energy = DCM.energy_in_kev.user_readback.get()

    # Use the lookup table to get the undulator gap associated with this dcm energy
    gap_to_match_dcm_energy = _get_closest_gap_to_dcm_energy(
        dcm_energy, energy_to_distance_table
    )

    # Check if undulator gap is close enough to the value from the DCM
    current_gap = undulator.gap.user_readback.get()

    if abs(gap_to_match_dcm_energy - current_gap) > undulator.gap_discrepancy_tolerance:
        LOGGER.warning(
            f"Undulator gap mismatch. {abs(gap_to_match_dcm_energy-current_gap):.3f} is outside tolerance.\
            Restoring gap to nominal value, {gap_to_match_dcm_energy}"
        )
        undulator.gap.set(gap_to_match_dcm_energy).wait(10)

    return True
