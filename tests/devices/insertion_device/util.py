import json

from pydantic import BaseModel

from dodal.devices.insertion_device import (
    ConfigServerEnergyMotorLookup,
    EnergyCoverage,
    EnergyMotorLookup,
    LookupTable,
    Pol,
)


class GenerateConfigLookupTable(BaseModel):
    polarisations: list[Pol]
    energy_coverage: list[EnergyCoverage]


def assert_expected_lut_file_equals_config_server_energy_motor_update_lookup_table(
    expected_lut_path: str,
    energy_motor_lookup: ConfigServerEnergyMotorLookup,
) -> None:
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
