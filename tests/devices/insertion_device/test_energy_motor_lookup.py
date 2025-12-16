from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dodal.devices.insertion_device.apple2_undulator import Pol
from dodal.devices.insertion_device.energy_motor_lookup import (
    ConfigServerEnergyMotorLookup,
    EnergyMotorLookup,
)
from dodal.devices.insertion_device.lookup_table_models import LookupTable
from tests.devices.insertion_device.util import (
    GenerateConfigLookupTable,
    assert_expected_lut_equals_energy_motor_update_after_update,
)


@pytest.fixture
def energy_motor_lookup(lut: LookupTable) -> EnergyMotorLookup:
    return EnergyMotorLookup(lut)


def test_energy_motor_lookup_find_value_in_lookup_table(
    energy_motor_lookup: EnergyMotorLookup,
    generate_config_lut: GenerateConfigLookupTable,
) -> None:
    for i in range(len(generate_config_lut.polarisations)):
        energy = generate_config_lut.energy_coverage[i].min_energy
        value = energy_motor_lookup.find_value_in_lookup_table(
            energy=energy,
            pol=generate_config_lut.polarisations[i],
        )
        expected_poly = generate_config_lut.energy_coverage[i].get_poly(energy)
        expected_value = expected_poly(energy)
        assert value == expected_value


def test_energy_motor_lookup_update_is_static(
    energy_motor_lookup: EnergyMotorLookup,
) -> None:
    before_update_lut = energy_motor_lookup.lut
    assert_expected_lut_equals_energy_motor_update_after_update(
        before_update_lut, energy_motor_lookup
    )


def test_energy_motor_lookup_find_value_in_lookup_table_updates_lut_if_lut_empty(
    energy_motor_lookup: EnergyMotorLookup,
    generate_config_lut: GenerateConfigLookupTable,
) -> None:
    energy = 100
    pol = Pol.LH

    mock_lut = MagicMock(wraps=LookupTable())
    # Set the lut data to empty to force an update
    mock_lut.root = {}
    mock_lut.get_poly.return_value = generate_config_lut.energy_coverage[0].get_poly(
        energy
    )

    # Replace methods and data with mocks
    energy_motor_lookup.lut = mock_lut
    mock_update_lut = MagicMock()
    energy_motor_lookup.update_lookup_table = mock_update_lut

    energy_motor_lookup.find_value_in_lookup_table(energy, pol)
    mock_update_lut.assert_called_once()
    mock_lut.get_poly.assert_called_once_with(energy=energy, pol=pol)


@pytest.fixture
def config_server_energy_motor_lookup() -> ConfigServerEnergyMotorLookup:
    return ConfigServerEnergyMotorLookup(MagicMock(), MagicMock(), Path("dummy_path"))


def test_config_server_energy_motor_lookup_update_lookup_table(
    config_server_energy_motor_lookup: ConfigServerEnergyMotorLookup,
    lut: LookupTable,
) -> None:
    assert config_server_energy_motor_lookup.lut == LookupTable()
    mock_read_lut = MagicMock(return_value=lut)
    config_server_energy_motor_lookup.read_lut = mock_read_lut

    config_server_energy_motor_lookup.find_value_in_lookup_table(100, Pol.LH)
    mock_read_lut.assert_called_once()
    assert config_server_energy_motor_lookup.lut == lut
