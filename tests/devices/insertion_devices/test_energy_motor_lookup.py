from collections import namedtuple

import pytest
from pytest import FixtureRequest

from dodal.devices.insertion_device.apple2_undulator import Pol
from dodal.devices.insertion_device.energy_motor_lookup import EnergyMotorLookup
from dodal.devices.insertion_device.lookup_table_models import (
    LookupTableConfig,
    generate_lookup_table,
)

Config = namedtuple(
    "Config", ["polarisations", "min_energies", "max_energies", "polys"]
)

TEST_PARAMS = [
    Config([Pol.LH], [100], [200], [[2.0, -1.0, 0.5]]),
    Config([Pol.LH, Pol.LV], [100, 200], [150.0, 250.0], [[1.0, 0.0], [0.5, 1.0]]),
]


@pytest.fixture(params=TEST_PARAMS)
def config(request: FixtureRequest) -> Config:
    return request.param


@pytest.fixture
def energy_motor_lookup(config: Config) -> EnergyMotorLookup:
    return EnergyMotorLookup(
        lut=generate_lookup_table(
            pols=config.polarisations,
            min_energies=config.min_energies,
            max_energies=config.max_energies,
            poly1d_params=config.polys,
        )
    )


def test_energy_motor_lookup_is_static(
    energy_motor_lookup: EnergyMotorLookup,
) -> None:
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
