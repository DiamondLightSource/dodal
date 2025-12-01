from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from dodal.devices.insertion_device.apple2_undulator import Pol
from dodal.devices.insertion_device.energy_motor_lookup import (
    ConfigServerEnergyMotorLookup,
    EnergyMotorLookup,
    get_poly,
)
from dodal.devices.insertion_device.lookup_table_models import LookupTable
from tests.devices.insertion_device.util import (
    GenerateConfigLookupTable,
    assert_expected_lut_equals_energy_motor_update_after_update,
)


@pytest.fixture
def energy_motor_lookup(lut: LookupTable) -> EnergyMotorLookup:
    return EnergyMotorLookup(lut)


def test_get_poly(
    lut: LookupTable, generate_config_lut: GenerateConfigLookupTable
) -> None:
    for i in range(len(generate_config_lut.polarisations)):
        expected_poly = np.poly1d(generate_config_lut.polys[i])
        poly = get_poly(
            energy=generate_config_lut.min_energies[i],
            pol=generate_config_lut.polarisations[i],
            lut=lut,
        )
        assert poly == expected_poly


def test_energy_motor_lookup_find_value_in_lookup_table(
    energy_motor_lookup: EnergyMotorLookup,
    generate_config_lut: GenerateConfigLookupTable,
) -> None:
    for i in range(len(generate_config_lut.polarisations)):
        value = energy_motor_lookup.find_value_in_lookup_table(
            energy=generate_config_lut.min_energies[i],
            pol=generate_config_lut.polarisations[i],
        )
        expected_poly = np.poly1d(generate_config_lut.polys[i])
        expected_value = expected_poly(generate_config_lut.min_energies[i])
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
) -> None:
    energy_motor_lookup.lut = LookupTable()
    mock_update_lut = MagicMock()
    energy_motor_lookup.update_lookup_table = mock_update_lut
    with patch("dodal.devices.insertion_device.energy_motor_lookup.get_poly"):
        energy_motor_lookup.find_value_in_lookup_table(100, Pol.LH)
        mock_update_lut.assert_called_once()


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
