from pathlib import Path

import pytest
from daq_config_server.client import ConfigServer
from ophyd_async.core import get_mock_put, init_devices

from dodal.devices.apple2_undulator import (
    Apple2,
    Pol,
    UndulatorGap,
    UndulatorPhaseAxes,
)
from dodal.devices.k07 import K07Apple2Controller
from dodal.devices.k07.insertion_device import (
    K07_GAP_POLY_DEG_COLUMNS,
    K07_PHASE_POLY_DEG_COLUMNS,
)
from dodal.devices.util.lookup_tables_apple2 import (
    ConfigServerEnergyMotorLookup,
    LookupTableConfig,
)
from tests.devices.k07.test_data import (
    TEST_SOFT_GAP_UNDULATOR_LUT,
    TEST_SOFT_PHASE_UNDULATOR_LUT,
)

# add mock_config_client, mock_id_gap, mock_phase and mock_jaw_phase_axes to pytest.
pytest_plugins = ["dodal.testing.fixtures.devices.apple2"]


@pytest.fixture
async def id(mock_id_gap: UndulatorGap, mock_phase_axes: UndulatorPhaseAxes) -> Apple2:
    async with init_devices(mock=True):
        mock_apple2 = Apple2(id_gap=mock_id_gap, id_phase=mock_phase_axes)
    return mock_apple2


@pytest.fixture
def mock_k07_gap_energy_motor_lookup(
    mock_config_client: ConfigServer,
) -> ConfigServerEnergyMotorLookup:
    return ConfigServerEnergyMotorLookup(
        lut_config=LookupTableConfig(poly_deg=K07_GAP_POLY_DEG_COLUMNS),
        config_client=mock_config_client,
        path=Path(TEST_SOFT_GAP_UNDULATOR_LUT),
    )


@pytest.fixture
def mock_k07_phase_energy_motor_lookup(
    mock_config_client: ConfigServer,
) -> ConfigServerEnergyMotorLookup:
    return ConfigServerEnergyMotorLookup(
        lut_config=LookupTableConfig(poly_deg=K07_PHASE_POLY_DEG_COLUMNS),
        config_client=mock_config_client,
        path=Path(TEST_SOFT_PHASE_UNDULATOR_LUT),
    )


@pytest.fixture
async def id_controller(
    id: Apple2,
    mock_k07_gap_energy_motor_lookup: ConfigServerEnergyMotorLookup,
    mock_k07_phase_energy_motor_lookup: ConfigServerEnergyMotorLookup,
) -> K07Apple2Controller:
    async with init_devices(mock=True):
        return K07Apple2Controller(
            apple2=id,
            gap_energy_motor_lut=mock_k07_gap_energy_motor_lookup,
            phase_energy_motor_lut=mock_k07_phase_energy_motor_lookup,
        )


# Insertion device controller does not exist yet - this class is a placeholder for when it does
@pytest.mark.parametrize(
    "pol, energy, expected_gap",
    [
        (Pol.LH, 0.3, 28),
        (Pol.LV, 0.5, 23),
        (Pol.PC, 1.1, 46),
        (Pol.NC, 0.8, 37),
        (Pol.LH3, 0.9, 28),
    ],
)
async def test_k07_apple2_controller_set_energy(
    id_controller: K07Apple2Controller,
    pol: Pol,
    energy: float,
    expected_gap: float,
):
    id_controller._polarisation_setpoint_set(pol)
    await id_controller.energy.set(energy)
    mock_gap_setpoint = get_mock_put(id_controller.apple2().gap().user_setpoint)
    assert float(mock_gap_setpoint.call_args_list[0].args[0]) == pytest.approx(
        expected_gap, abs=1
    )
