import json
from collections import namedtuple

from dodal.devices.insertion_device.energy_motor_lookup import (
    ConfigServerEnergyMotorLookup,
    EnergyMotorLookup,
)
from dodal.devices.insertion_device.lookup_table_models import LookupTable

GenerateConfigLookupTable = namedtuple(
    "GenerateConfigLookupTable",
    ["polarisations", "min_energies", "max_energies", "polys"],
)


def assert_expected_lut_file_equals_config_server_energy_motor_update_lookup_table(
    expected_lut_path: str,
    energy_motor_lookup: ConfigServerEnergyMotorLookup,
) -> None:
    # Should we add default test here and each beamline adds there config_server_energy_motor_lookup or be done in apple2 file?
    with open(expected_lut_path, "rb") as f:
        expected_lut = LookupTable(json.load(f))
    assert_expected_lut_equals_energy_motor_update_after_update(
        expected_lut, energy_motor_lookup
    )


def assert_expected_lut_equals_energy_motor_update_after_update(
    expected_lut: LookupTable,
    energy_motor_lookup: EnergyMotorLookup,
) -> None:
    energy_motor_lookup.update_lookup_table()
    assert energy_motor_lookup.lut == expected_lut
