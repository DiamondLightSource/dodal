import numpy as np
import pytest

from dodal.devices.insertion_device.energy_motor_lookup import (
    EnergyMotorLookup,
    get_poly,
)
from dodal.devices.insertion_device.lookup_table_models import LookupTable
from tests.devices.insertion_devices.conftest import GenerateConfigLookupTable
from tests.devices.insertion_devices.util import (
    assert_expected_lut_equals_energy_motor_update_after_update,
)

# add mock_config_client to pytest
pytest_plugins = ["dodal.testing.fixtures.devices.apple2"]


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


# @pytest.fixture
# def lut_config() -> LookupTableConfig:
#     return LookupTableConfig(
#         mode="Mode",
#         min_energy="MinEnergy",
#         max_energy="MaxEnergy",
#         poly_deg=["c1", "c0"],
#         mode_name_convert={"hl": "lh", "vl": "lv"},
#     )


# @pytest.fixture
# def config_server_energy_motor_lookup(
#     lut_config: LookupTableConfig,
#     config_server: ConfigServer,
#     path: Path,
# ) -> ConfigServerEnergyMotorLookup:
#     return ConfigServerEnergyMotorLookup(config_server, lut_config, path)


# def test_config_server_energy_motor_lookup_read_lut(
#     config_server_energy_motor_lookup: ConfigServerEnergyMotorLookup,
# ) -> None:
#     # Should we add default test here and each beamline adds there config_server_energy_motor_lookup or be done in apple2 file?
#     pass
