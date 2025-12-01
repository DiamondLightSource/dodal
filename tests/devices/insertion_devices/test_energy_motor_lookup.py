import pytest

from dodal.devices.insertion_device.energy_motor_lookup import EnergyMotorLookup
from dodal.devices.insertion_device.lookup_table_models import (
    LookupTable,
    LookupTableConfig,
)


@pytest.fixture
def energy_motor_lookup(lut: LookupTable) -> EnergyMotorLookup:
    return EnergyMotorLookup(lut)


def test_energy_motor_lookup_is_static(energy_motor_lookup: EnergyMotorLookup) -> None:
    before_update_lut = energy_motor_lookup.lut
    energy_motor_lookup.update_lookup_table()
    after_update_lut = energy_motor_lookup.lut
    assert before_update_lut == after_update_lut


@pytest.fixture
def lut_config() -> LookupTableConfig:
    return LookupTableConfig(
        mode="Mode",
        min_energy="MinEnergy",
        max_energy="MaxEnergy",
        poly_deg=["c1", "c0"],
        mode_name_convert={"hl": "lh", "vl": "lv"},
    )
