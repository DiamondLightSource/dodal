from pathlib import Path
from unittest.mock import call

import pytest
from daq_config_server.client import ConfigServer
from ophyd_async.core import (
    get_mock_put,
    init_devices,
    set_mock_value,
)

from dodal.devices.i09_2_shared.i09_apple2 import (
    J09_GAP_POLY_DEG_COLUMNS,
    J09_PHASE_POLY_DEG_COLUMNS,
    J09Apple2Controller,
)
from dodal.devices.insertion_device.apple2_undulator import (
    Apple2,
    BeamEnergy,
    InsertionDeviceEnergy,
    InsertionDevicePolarisation,
    Pol,
    UndulatorGap,
    UndulatorPhaseAxes,
)
from dodal.devices.insertion_device.energy_motor_lookup import (
    ConfigServerEnergyMotorLookup,
)
from dodal.devices.insertion_device.lookup_table_models import (
    MAXIMUM_ROW_PHASE_MOTOR_POSITION,
    ROW_PHASE_CIRCULAR,
    LookupTableColumnConfig,
)
from dodal.devices.pgm import PlaneGratingMonochromator
from tests.devices.i09_2_shared.test_data import (
    TEST_EXPECTED_SOFT_GAP_UNDULATOR_LUT,
    TEST_EXPECTED_SOFT_PHASE_UNDULATOR_LUT,
    TEST_SOFT_GAP_UNDULATOR_LUT,
    TEST_SOFT_PHASE_UNDULATOR_LUT,
)
from tests.devices.insertion_device.util import (
    assert_expected_lut_file_equals_config_server_energy_motor_update_lookup_table,
)

# add mock_config_client, mock_id_gap, mock_phase and mock_jaw_phase_axes to pytest.
pytest_plugins = ["dodal.testing.fixtures.devices.apple2"]


@pytest.fixture
def mock_j09_gap_energy_motor_lookup(
    mock_config_client: ConfigServer,
) -> ConfigServerEnergyMotorLookup:
    return ConfigServerEnergyMotorLookup(
        lut_config=LookupTableColumnConfig(poly_deg=J09_GAP_POLY_DEG_COLUMNS),
        config_client=mock_config_client,
        path=Path(TEST_SOFT_GAP_UNDULATOR_LUT),
    )


@pytest.fixture
def mock_j09_phase_energy_motor_lookup(
    mock_config_client: ConfigServer,
) -> ConfigServerEnergyMotorLookup:
    return ConfigServerEnergyMotorLookup(
        lut_config=LookupTableColumnConfig(poly_deg=J09_PHASE_POLY_DEG_COLUMNS),
        config_client=mock_config_client,
        path=Path(TEST_SOFT_PHASE_UNDULATOR_LUT),
    )


@pytest.fixture
async def mock_apple2(
    mock_id_gap: UndulatorGap, mock_phase_axes: UndulatorPhaseAxes
) -> Apple2:
    async with init_devices(mock=True):
        mock_apple2 = Apple2(id_gap=mock_id_gap, id_phase=mock_phase_axes)
    return mock_apple2


@pytest.fixture
async def mock_id_controller(
    mock_apple2: Apple2,
    mock_j09_gap_energy_motor_lookup: ConfigServerEnergyMotorLookup,
    mock_j09_phase_energy_motor_lookup: ConfigServerEnergyMotorLookup,
) -> J09Apple2Controller:
    async with init_devices(mock=True):
        mock_id_controller = J09Apple2Controller(
            apple2=mock_apple2,
            gap_energy_motor_lut=mock_j09_gap_energy_motor_lookup,
            phase_energy_motor_lut=mock_j09_phase_energy_motor_lookup,
        )
    mock_id_controller._energy_set(0.5)
    return mock_id_controller


@pytest.fixture
async def mock_id_energy(
    mock_id_controller: J09Apple2Controller,
) -> InsertionDeviceEnergy:
    async with init_devices(mock=True):
        mock_id_energy = InsertionDeviceEnergy(
            id_controller=mock_id_controller,
        )

    return mock_id_energy


@pytest.fixture
async def beam_energy(
    mock_id_energy: InsertionDeviceEnergy, mock_pgm: PlaneGratingMonochromator
) -> BeamEnergy:
    async with init_devices(mock=True):
        beam_energy = BeamEnergy(id_energy=mock_id_energy, mono=mock_pgm.energy)
    return beam_energy


@pytest.fixture
async def mock_id_pol(
    mock_id_controller: J09Apple2Controller,
) -> InsertionDevicePolarisation:
    async with init_devices(mock=True):
        mock_id_pol = InsertionDevicePolarisation(id_controller=mock_id_controller)

    return mock_id_pol


def test_j09_energy_motor_lookup_update_lut_success(
    mock_j09_gap_energy_motor_lookup: ConfigServerEnergyMotorLookup,
    mock_j09_phase_energy_motor_lookup: ConfigServerEnergyMotorLookup,
):
    assert_expected_lut_file_equals_config_server_energy_motor_update_lookup_table(
        TEST_EXPECTED_SOFT_GAP_UNDULATOR_LUT, mock_j09_gap_energy_motor_lookup
    )
    assert_expected_lut_file_equals_config_server_energy_motor_update_lookup_table(
        TEST_EXPECTED_SOFT_PHASE_UNDULATOR_LUT, mock_j09_phase_energy_motor_lookup
    )


@pytest.mark.parametrize(
    "pol, top_outer_phase,top_inner_phase,btm_inner_phase, btm_outer_phase",
    [
        (Pol.LH, 0, 0, 0, 0),
        (Pol.LV, 24.0, 0, 24.0, 0),
        (Pol.PC, 12, 0, 12, 0),
        (Pol.NC, -12, 0, -12, 0),
        (Pol.NONE, 8, 12, 2, -12),
    ],
)
async def test_j09_apple2_controller_determine_pol(
    mock_id_controller: J09Apple2Controller,
    pol: Pol,
    top_inner_phase: float,
    top_outer_phase: float,
    btm_inner_phase: float,
    btm_outer_phase: float,
):
    assert await mock_id_controller.polarisation_setpoint.get_value() == Pol.NONE

    set_mock_value(
        mock_id_controller.apple2().phase().top_inner.user_readback, top_inner_phase
    )
    set_mock_value(
        mock_id_controller.apple2().phase().top_outer.user_readback, top_outer_phase
    )
    set_mock_value(
        mock_id_controller.apple2().phase().btm_inner.user_readback, btm_inner_phase
    )
    set_mock_value(
        mock_id_controller.apple2().phase().btm_outer.user_readback, btm_outer_phase
    )
    if pol == Pol.NONE:
        with pytest.raises(ValueError):
            await mock_id_controller.energy.set(0.800)
    else:
        await mock_id_controller.energy.set(0.800)
        assert await mock_id_controller.polarisation.get_value() == pol


@pytest.mark.parametrize(
    "pol, top_outer_phase,top_inner_phase,btm_inner_phase, btm_outer_phase",
    [
        (
            Pol.LH,
            0.0,
            0.0,
            0.0,
            0.0,
        ),
    ],
)
async def test_j09_apple2_controller_set_pol_lh(
    mock_id_controller: J09Apple2Controller,
    pol: Pol,
    top_inner_phase: float,
    top_outer_phase: float,
    btm_inner_phase: float,
    btm_outer_phase: float,
):
    await mock_id_controller.polarisation.set(pol)
    get_mock_put(
        mock_id_controller.apple2().phase().top_outer.user_setpoint
    ).assert_called_once_with(f"{top_outer_phase:.6f}", wait=True)
    get_mock_put(
        mock_id_controller.apple2().phase().top_inner.user_setpoint
    ).assert_called_once_with(f"{top_inner_phase:.6f}", wait=True)
    get_mock_put(
        mock_id_controller.apple2().phase().btm_inner.user_setpoint
    ).assert_called_once_with(f"{btm_inner_phase:.6f}", wait=True)
    get_mock_put(
        mock_id_controller.apple2().phase().btm_outer.user_setpoint
    ).assert_called_once_with(f"{btm_outer_phase:.6f}", wait=True)


@pytest.mark.parametrize(
    "pol, top_outer_phase,top_inner_phase,btm_inner_phase, btm_outer_phase",
    [
        (
            Pol.LV,
            MAXIMUM_ROW_PHASE_MOTOR_POSITION,
            0.0,
            MAXIMUM_ROW_PHASE_MOTOR_POSITION,
            0.0,
        ),
        (Pol.PC, ROW_PHASE_CIRCULAR, 0.0, ROW_PHASE_CIRCULAR, 0.0),
        (Pol.NC, -ROW_PHASE_CIRCULAR, 0.0, -ROW_PHASE_CIRCULAR, 0.0),
    ],
)
async def test_j09_apple2_controller_set_pol(
    mock_id_controller: J09Apple2Controller,
    pol: Pol,
    top_inner_phase: float,
    top_outer_phase: float,
    btm_inner_phase: float,
    btm_outer_phase: float,
):
    mock_id_controller.gap_energy_motor_lut.update_lookup_table()
    mock_id_controller.phase_energy_motor_lut.update_lookup_table()
    await mock_id_controller.polarisation.set(pol)
    assert get_mock_put(
        mock_id_controller.apple2().phase().top_outer.user_setpoint
    ).call_args_list == [
        call(f"{0:.6f}", wait=True),
        call(f"{top_outer_phase:.6f}", wait=True),
    ]
    assert get_mock_put(
        mock_id_controller.apple2().phase().top_inner.user_setpoint
    ).call_args_list == [
        call(f"{0:.6f}", wait=True),
        call(f"{top_inner_phase:.6f}", wait=True),
    ]
    assert get_mock_put(
        mock_id_controller.apple2().phase().btm_inner.user_setpoint
    ).call_args_list == [
        call(f"{0:.6f}", wait=True),
        call(f"{btm_inner_phase:.6f}", wait=True),
    ]
    assert get_mock_put(
        mock_id_controller.apple2().phase().btm_outer.user_setpoint
    ).call_args_list == [
        call(f"{0:.6f}", wait=True),
        call(f"{btm_outer_phase:.6f}", wait=True),
    ]


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
async def test_j09_apple2_controller_set_energy(
    mock_id_controller: J09Apple2Controller,
    pol: Pol,
    energy: float,
    expected_gap: float,
):
    mock_id_controller._polarisation_setpoint_set(pol)
    await mock_id_controller.energy.set(energy)
    mock_gap_setpoint = get_mock_put(mock_id_controller.apple2().gap().user_setpoint)
    assert float(mock_gap_setpoint.call_args_list[0].args[0]) == pytest.approx(
        expected_gap, abs=1
    )
