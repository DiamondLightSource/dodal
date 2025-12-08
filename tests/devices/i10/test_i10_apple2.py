from collections.abc import Mapping
from pathlib import Path
from unittest import mock
from unittest.mock import AsyncMock, Mock

import pytest
from bluesky.plans import scan
from bluesky.run_engine import RunEngine
from daq_config_server.client import ConfigServer
from numpy import linspace, poly1d
from ophyd_async.core import (
    callback_on_mock_put,
    get_mock_put,
    init_devices,
    set_mock_value,
)
from ophyd_async.testing import assert_emitted

from dodal.devices.i10.i10_apple2 import (
    DEFAULT_JAW_PHASE_POLY_PARAMS,
    I10Apple2,
    I10Apple2Controller,
    LinearArbitraryAngle,
)
from dodal.devices.i10.i10_setting_data import I10Grating
from dodal.devices.insertion_device.apple2_undulator import (
    MAXIMUM_MOVE_TIME,
    BeamEnergy,
    EnabledDisabledUpper,
    InsertionDeviceEnergy,
    InsertionDevicePolarisation,
    Pol,
    UndulatorGap,
    UndulatorGateStatus,
    UndulatorJawPhase,
    UndulatorPhaseAxes,
)
from dodal.devices.insertion_device.energy_motor_lookup import (
    ConfigServerEnergyMotorLookup,
)
from dodal.devices.insertion_device.lookup_table_models import (
    EnergyCoverage,
    EnergyCoverageEntry,
    LookupTableColumnConfig,
    Source,
)
from dodal.devices.pgm import PlaneGratingMonochromator
from tests.devices.i10.test_data import (
    EXPECTED_ID_ENERGY_2_GAP_CALIBRATIONS_IDD_JSON,
    EXPECTED_ID_ENERGY_2_GAP_CALIBRATIONS_IDU_JSON,
    EXPECTED_ID_ENERGY_2_PHASE_CALIBRATIONS_IDD_JSON,
    EXPECTED_ID_ENERGY_2_PHASE_CALIBRATIONS_IDU_JSON,
    ID_ENERGY_2_GAP_CALIBRATIONS_CSV,
    ID_ENERGY_2_PHASE_CALIBRATIONS_CSV,
)
from tests.devices.insertion_device.util import (
    assert_expected_lut_file_equals_config_server_energy_motor_update_lookup_table,
)

# add mock_config_client, mock_id_gap, mock_phase and mock_jaw_phase_axes to pytest.
pytest_plugins = ["dodal.testing.fixtures.devices.apple2"]


@pytest.fixture
async def mock_pgm(prefix: str = "BLXX-EA-DET-007:") -> PlaneGratingMonochromator:
    async with init_devices(mock=True):
        mock_pgm = PlaneGratingMonochromator(
            prefix=prefix, grating=I10Grating, grating_pv="NLINES2"
        )
    return mock_pgm


@pytest.fixture
async def mock_id(
    mock_id_gap: UndulatorGap,
    mock_phase_axes: UndulatorPhaseAxes,
    mock_jaw_phase: UndulatorJawPhase,
) -> I10Apple2:
    async with init_devices(mock=True):
        mock_id = I10Apple2(
            id_gap=mock_id_gap, id_phase=mock_phase_axes, id_jaw_phase=mock_jaw_phase
        )
    return mock_id


@pytest.fixture
def mock_i10_gap_energy_motor_lookup_idu(
    mock_config_client: ConfigServer,
) -> ConfigServerEnergyMotorLookup:
    return ConfigServerEnergyMotorLookup(
        config_client=mock_config_client,
        lut_config=LookupTableColumnConfig(source=Source(column="Source", value="idu")),
        path=Path(ID_ENERGY_2_GAP_CALIBRATIONS_CSV),
    )


@pytest.fixture
def mock_i10_phase_energy_motor_lookup_idu(
    mock_config_client: ConfigServer,
) -> ConfigServerEnergyMotorLookup:
    return ConfigServerEnergyMotorLookup(
        config_client=mock_config_client,
        lut_config=LookupTableColumnConfig(source=Source(column="Source", value="idu")),
        path=Path(ID_ENERGY_2_PHASE_CALIBRATIONS_CSV),
    )


@pytest.fixture
def mock_i10_gap_energy_motor_lookup_idd(
    mock_config_client: ConfigServer,
) -> ConfigServerEnergyMotorLookup:
    return ConfigServerEnergyMotorLookup(
        config_client=mock_config_client,
        lut_config=LookupTableColumnConfig(source=Source(column="Source", value="idd")),
        path=Path(ID_ENERGY_2_GAP_CALIBRATIONS_CSV),
    )


@pytest.fixture
def mock_i10_phase_energy_motor_lookup_idd(
    mock_config_client: ConfigServer,
) -> ConfigServerEnergyMotorLookup:
    return ConfigServerEnergyMotorLookup(
        config_client=mock_config_client,
        lut_config=LookupTableColumnConfig(source=Source(column="Source", value="idd")),
        path=Path(ID_ENERGY_2_PHASE_CALIBRATIONS_CSV),
    )


@pytest.fixture
async def mock_id_controller(
    mock_id: I10Apple2,
    mock_i10_gap_energy_motor_lookup_idu: ConfigServerEnergyMotorLookup,
    mock_i10_phase_energy_motor_lookup_idu: ConfigServerEnergyMotorLookup,
) -> I10Apple2Controller:
    async with init_devices(mock=True):
        mock_id_controller = I10Apple2Controller(
            apple2=mock_id,
            gap_energy_motor_lut=mock_i10_gap_energy_motor_lookup_idu,
            phase_energy_motor_lut=mock_i10_phase_energy_motor_lookup_idu,
        )

    return mock_id_controller


@pytest.fixture
async def mock_id_energy(
    mock_id_controller: I10Apple2Controller,
) -> InsertionDeviceEnergy:
    async with init_devices(mock=True):
        mock_id_energy = InsertionDeviceEnergy(id_controller=mock_id_controller)
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
    mock_id_controller: I10Apple2Controller,
) -> InsertionDevicePolarisation:
    async with init_devices(mock=True):
        mock_id_pol = InsertionDevicePolarisation(id_controller=mock_id_controller)

    return mock_id_pol


@pytest.fixture
async def mock_linear_arbitrary_angle(
    mock_id_controller: I10Apple2Controller,
) -> LinearArbitraryAngle:
    async with init_devices(mock=True):
        mock_linear_arbitrary_angle = LinearArbitraryAngle(
            id_controller=mock_id_controller
        )
    return mock_linear_arbitrary_angle


@pytest.mark.parametrize(
    "pol, top_outer_phase,top_inner_phase,btm_inner_phase, btm_outer_phase",
    [
        (Pol.LH, 0, 0, 0, 0),
        (Pol.LV, 24.0, 0, 24.0, 0),
        (Pol.PC, 12, 0, 12, 0),
        (Pol.NC, -12, 0, -12, 0),
        (Pol.LA, 12, 0, -12, 0),
        (Pol.LA, 0, 12, 0, -12),
        (Pol.LA, -11, 0, 11, 0),
        (Pol.NONE, 8, 12, 2, -12),
        (Pol.NONE, 11, 0, 10, 0),
    ],
)
async def test_i10_apple2_controller_determine_pol(
    mock_id_controller: I10Apple2Controller,
    pol: None | str,
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
            await mock_id_controller.energy.set(800)
    else:
        await mock_id_controller.energy.set(800)
        assert await mock_id_controller.polarisation.get_value() == pol


async def test_fail_i10_apple2_controller_set_undefined_pol(
    mock_id_controller: I10Apple2Controller,
):
    set_mock_value(mock_id_controller.apple2().gap().user_readback, 101)
    with pytest.raises(RuntimeError) as e:
        await mock_id_controller.energy.set(600)
    assert (
        str(e.value)
        == mock_id_controller.name
        + " is not in use, close gap or set polarisation to use this ID"
    )


async def test_fail_i10_apple2_controller_set_id_not_ready(
    mock_id_controller: I10Apple2Controller,
):
    set_mock_value(
        mock_id_controller.apple2().gap().status, EnabledDisabledUpper.DISABLED
    )
    with pytest.raises(RuntimeError) as e:
        await mock_id_controller.energy.set(600)
    assert (
        str(e.value)
        == mock_id_controller.apple2().gap().name + " is DISABLED and cannot move."
    )
    set_mock_value(
        mock_id_controller.apple2().gap().status, EnabledDisabledUpper.ENABLED
    )
    set_mock_value(mock_id_controller.apple2().gap().gate, UndulatorGateStatus.OPEN)
    with pytest.raises(RuntimeError) as e:
        await mock_id_controller.energy.set(600)
    assert (
        str(e.value)
        == mock_id_controller.apple2().gap().name + " is already in motion."
    )


async def test_fail_i10_apple2_controller_set_energy_has_default(
    mock_id_energy: InsertionDeviceEnergy,
    mock_id_controller: I10Apple2Controller,
):
    mock_id_controller.energy.set = AsyncMock()
    await mock_id_energy.set(600)
    mock_id_controller.energy.set.assert_awaited_once_with(
        600, timeout=MAXIMUM_MOVE_TIME
    )


async def test_beam_energy_re_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    beam_energy: BeamEnergy,
):
    run_engine(scan([], beam_energy, 500, 600, num=11))
    assert_emitted(run_engine_documents, start=1, descriptor=1, event=11, stop=1)

    for cnt, data in enumerate(run_engine_documents["event"]):
        assert data["data"]["mock_id_controller-energy"] == 500 + cnt * 10
        assert data["data"]["mock_pgm-energy"] == 500 + cnt * 10


async def test_beam_energy_re_scan_with_offset(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    beam_energy: BeamEnergy,
    mock_id_controller: I10Apple2Controller,
):
    mock_id_controller._polarisation_setpoint_set(Pol.LH3)
    # with energy offset
    await beam_energy.id_energy_offset.set(20)
    rbv_mocks = Mock()
    rbv_mocks.get.side_effect = range(1700, 1810, 10)
    callback_on_mock_put(
        beam_energy._mono_energy().user_setpoint,
        lambda *_, **__: set_mock_value(
            beam_energy._mono_energy().user_readback, rbv_mocks.get()
        ),
    )
    run_engine(scan([], beam_energy, 1700, 1800, num=11))

    for cnt, data in enumerate(run_engine_documents["event"]):
        assert data["data"]["mock_id_controller-energy"] == 1700 + cnt * 10 + 20
        assert data["data"]["mock_pgm-energy"] == 1700 + cnt * 10


@pytest.mark.parametrize(
    "pol,energy, expect_top_outer, expect_top_inner, expect_btm_inner,expect_btm_outer, expect_gap",
    [
        (Pol.LH, 500, 0.0, 0.0, 0.0, 0.0, 23.0),
        (Pol.LH, 700, 0.0, 0.0, 0.0, 0.0, 26.0),
        (Pol.LH, 1000, 0.0, 0.0, 0.0, 0.0, 32.0),
        (Pol.LH, 1400, 0.0, 0.0, 0.0, 0.0, 40.11),
        (Pol.LH3, 1400, 0.0, 0.0, 0.0, 0.0, 21.8),  # force LH3 lookup table to be used
        (Pol.LH3, 1700, 0.0, 0.0, 0.0, 0.0, 23.93),
        (Pol.LH3, 1900, 0.0, 0.0, 0.0, 0.0, 25.0),
        (Pol.LH3, 2090, 0.0, 0.0, 0.0, 0.0, 26.0),
        (Pol.LV, 600, 24.0, 0.0, 24.0, 0.0, 17.0),
        (Pol.LV, 900, 24.0, 0.0, 24.0, 0.0, 21.0),
        (Pol.LV, 1200, 24.0, 0.0, 24.0, 0.0, 25.0),
        (Pol.PC, 500, 15.5, 0.0, 15.5, 0.0, 17.0),
        (Pol.PC, 700, 16, 0.0, 16, 0.0, 21.0),
        (Pol.PC, 1000, 16.5, 0.0, 16.5, 0.0, 25.0),
        (Pol.NC, 500, -15.5, 0.0, -15.5, 0.0, 17.0),
        (Pol.NC, 800, -16, 0.0, -16, 0.0, 22.0),
        (Pol.NC, 1000, -16.5, 0.0, -16.5, 0.0, 25.0),
        (Pol.LA, 700, -15.2, 0.0, 15.2, 0.0, 16.5),
        (Pol.LA, 900, -15.6, 0.0, 15.6, 0.0, 19.0),
        (Pol.LA, 1300, -16.4, 0.0, 16.4, 0.0, 25.0),
        ("dsf", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
    ],
)
async def test_id_polarisation_set(
    mock_id_pol: InsertionDevicePolarisation,
    mock_id_controller: I10Apple2Controller,
    pol: Pol,
    energy: float,
    expect_top_inner: float,
    expect_top_outer: float,
    expect_btm_inner: float,
    expect_btm_outer: float,
    expect_gap: float,
):
    set_mock_value(mock_id_controller._energy, energy)

    if pol == "dsf":
        with pytest.raises(ValueError):
            await mock_id_pol.set(pol)
    else:
        await mock_id_pol.set(pol)

        top_inner = get_mock_put(
            mock_id_controller.apple2().phase().top_inner.user_setpoint
        )
        top_inner.assert_called_once()
        assert float(top_inner.call_args[0][0]) == pytest.approx(expect_top_inner, 0.01)

        top_outer = get_mock_put(
            mock_id_controller.apple2().phase().top_outer.user_setpoint
        )
        top_outer.assert_called_once()
        assert float(top_outer.call_args[0][0]) == pytest.approx(expect_top_outer, 0.01)

        btm_inner = get_mock_put(
            mock_id_controller.apple2().phase().btm_inner.user_setpoint
        )
        btm_inner.assert_called_once()
        assert float(btm_inner.call_args[0][0]) == pytest.approx(expect_btm_inner, 0.01)

        btm_outer = get_mock_put(
            mock_id_controller.apple2().phase().btm_outer.user_setpoint
        )
        btm_outer.assert_called_once()
        assert float(btm_outer.call_args[0][0]) == pytest.approx(expect_btm_outer, 0.01)

        gap = get_mock_put(mock_id_controller.apple2().gap().user_setpoint)
        gap.assert_called_once()
        assert float(gap.call_args[0][0]) == pytest.approx(expect_gap, 0.05)


async def test_id_polarisation_set_has_default_timeout(
    mock_id_pol: InsertionDevicePolarisation,
    mock_id_controller: I10Apple2Controller,
):
    set_mock_value(mock_id_controller._energy, 700)
    mock_id_controller.polarisation.set = AsyncMock()
    await mock_id_pol.set(Pol.LV)
    mock_id_controller.polarisation.set.assert_awaited_once_with(
        Pol.LV, timeout=MAXIMUM_MOVE_TIME
    )


@pytest.mark.parametrize(
    "pol,energy, top_outer, top_inner, btm_inner,btm_outer",
    [
        (Pol.LH, 550, 0.0, 0.0, 0.0, 0.0),
        (Pol.LV, 600, 24.0, 0.0, 24.0, 0.0),
        (Pol.PC, 550, 15.5, 0.0, 15.5, 0.0),
        (Pol.NC, 550, -15.5, 0.0, -15.5, 0.0),
        (Pol.LA, 1300, -16.4, 0.0, 16.4, 0.0),
    ],
)
async def test_id_polarisation_locate(
    mock_id_pol: InsertionDevicePolarisation,
    mock_id_controller: I10Apple2Controller,
    pol: Pol,
    energy: float,
    top_inner: float,
    top_outer: float,
    btm_inner: float,
    btm_outer: float,
):
    await mock_id_controller.energy.set(energy)

    await mock_id_pol.set(pol=pol)
    assert await mock_id_pol.locate() == {"setpoint": pol, "readback": Pol.LH}
    # move the motor
    set_mock_value(
        mock_id_controller.apple2().phase().top_inner.user_readback, top_inner
    )
    set_mock_value(
        mock_id_controller.apple2().phase().top_outer.user_readback, top_outer
    )
    set_mock_value(
        mock_id_controller.apple2().phase().btm_inner.user_readback, btm_inner
    )
    set_mock_value(
        mock_id_controller.apple2().phase().btm_outer.user_readback, btm_outer
    )
    assert await mock_id_pol.locate() == {"setpoint": pol, "readback": pol}


@pytest.mark.parametrize(
    "pol,energy, top_outer, top_inner, btm_inner,btm_outer",
    [
        (Pol.LH, 500, 0.0, 0.0, 0.0, 0.0),
        (Pol.LV, 600, 24.0, 0.0, 24.0, 0.0),
        (Pol.PC, 500, 15.5, 0.0, 15.5, 0.0),
        (Pol.NC, 500, -15.5, 0.0, -15.5, 0.0),
        (Pol.LA, 1300, -16.4, 0.0, 16.4, 0.0),
    ],
)
async def test_id_polarisation_read_check_pol_from_hardware(
    mock_id_pol: InsertionDevicePolarisation,
    mock_id_controller: I10Apple2Controller,
    pol: str,
    energy: float,
    top_inner: float,
    top_outer: float,
    btm_inner: float,
    btm_outer: float,
):
    set_mock_value(mock_id_controller._energy, energy)

    set_mock_value(
        mock_id_controller.apple2().phase().top_inner.user_readback, top_inner
    )
    set_mock_value(
        mock_id_controller.apple2().phase().top_outer.user_readback, top_outer
    )
    set_mock_value(
        mock_id_controller.apple2().phase().btm_inner.user_readback, btm_inner
    )
    set_mock_value(
        mock_id_controller.apple2().phase().btm_outer.user_readback, btm_outer
    )

    assert (await mock_id_pol.read())["mock_id_controller-polarisation"]["value"] == pol


@pytest.mark.parametrize(
    "pol,energy, top_outer, top_inner, btm_inner,btm_outer",
    [
        (Pol.LH3, 500, 0.0, 0.0, 0.0, 0.0),
    ],
)
async def test_id_polarisation_read_leave_lh3_unchanged_when_hardware_match(
    mock_id_pol: InsertionDevicePolarisation,
    mock_id_controller: I10Apple2Controller,
    pol: Pol,
    energy: float,
    top_inner: float,
    top_outer: float,
    btm_inner: float,
    btm_outer: float,
):
    set_mock_value(mock_id_controller._energy, energy)
    mock_id_controller._polarisation_setpoint_set(Pol.LH3)
    set_mock_value(
        mock_id_controller.apple2().phase().top_inner.user_readback, top_inner
    )
    set_mock_value(
        mock_id_controller.apple2().phase().top_outer.user_readback, top_outer
    )
    set_mock_value(
        mock_id_controller.apple2().phase().btm_inner.user_readback, btm_inner
    )
    set_mock_value(
        mock_id_controller.apple2().phase().btm_outer.user_readback, btm_outer
    )
    assert (await mock_id_pol.read())["mock_id_controller-polarisation"]["value"] == pol


async def test_linear_arbitrary_pol_fail_set(
    mock_linear_arbitrary_angle: LinearArbitraryAngle,
    mock_id_controller: I10Apple2Controller,
):
    with pytest.raises(RuntimeError) as e:
        await mock_linear_arbitrary_angle.set(20)
    assert str(e.value) == (
        f"Angle control is not available in polarisation"
        f" {await mock_id_controller.polarisation.get_value()}"
        + f" with {mock_id_controller.name}"
    )


async def test_linear_arbitrary_pol_fail_read(
    mock_linear_arbitrary_angle: LinearArbitraryAngle,
    mock_id_controller: I10Apple2Controller,
):
    with pytest.raises(RuntimeError) as e:
        await mock_linear_arbitrary_angle.read()
    assert str(e.value) == (
        f"Angle control is not available in polarisation"
        f" {await mock_id_controller.polarisation.get_value()}"
        + f" with {mock_id_controller.name}"
    )


async def test_linear_arbitrary_pol_set_default_timeout(
    mock_linear_arbitrary_angle: LinearArbitraryAngle,
    mock_id_controller: I10Apple2Controller,
):
    mock_id_controller.linear_arbitrary_angle.set = AsyncMock()
    await mock_linear_arbitrary_angle.set(60)
    mock_id_controller.linear_arbitrary_angle.set.assert_awaited_once_with(
        60, timeout=MAXIMUM_MOVE_TIME
    )


@pytest.mark.parametrize(
    "poly",
    [18, -18, 12.01, -12.01],
)
async def test_linear_arbitrary_limit_fail(
    mock_linear_arbitrary_angle: LinearArbitraryAngle,
    mock_id_controller: I10Apple2Controller,
    poly: float,
):
    set_mock_value(
        mock_id_controller.apple2().phase().top_inner.user_readback,
        16.4,
    )
    set_mock_value(
        mock_id_controller.apple2().phase().top_outer.user_readback,
        0,
    )
    set_mock_value(
        mock_id_controller.apple2().phase().btm_inner.user_readback,
        0,
    )
    set_mock_value(
        mock_id_controller.apple2().phase().btm_outer.user_readback,
        -16.4,
    )
    mock_id_controller.jaw_phase_from_angle = poly1d([poly])
    with pytest.raises(RuntimeError) as e:
        await mock_linear_arbitrary_angle.set(20.0)
    assert (
        str(e.value)
        == f"jaw_phase position for angle (20.0) is outside permitted range"
        f" [-{mock_id_controller.jaw_phase_limit},"
        f" {mock_id_controller.jaw_phase_limit}]"
    )


@pytest.mark.parametrize(
    "start, stop, num_point",
    [
        (-1, 180, 11),
        (-20, 170, 31),
        (-90, -25, 18),
    ],
)
async def test_linear_arbitrary_run_engine_scan(
    run_engine: RunEngine,
    run_engine_documents: Mapping[str, list[dict]],
    mock_linear_arbitrary_angle: LinearArbitraryAngle,
    mock_id_controller: I10Apple2Controller,
    start: float,
    stop: float,
    num_point: int,
):
    angles = linspace(start, stop, num_point, endpoint=True)

    set_mock_value(
        mock_id_controller.apple2().phase().top_inner.user_readback,
        16.4,
    )
    set_mock_value(
        mock_id_controller.apple2().phase().top_outer.user_readback,
        0,
    )
    set_mock_value(
        mock_id_controller.apple2().phase().btm_inner.user_readback,
        0,
    )
    set_mock_value(
        mock_id_controller.apple2().phase().btm_outer.user_readback,
        -16.4,
    )
    run_engine(
        scan(
            [],
            mock_linear_arbitrary_angle,
            start,
            stop,
            num=num_point,
        ),
    )
    assert_emitted(run_engine_documents, start=1, descriptor=1, event=num_point, stop=1)
    set_mock_value(
        mock_id_controller.apple2().gap().gate,
        UndulatorGateStatus.CLOSE,
    )
    set_mock_value(
        mock_id_controller.apple2().phase().gate,
        UndulatorGateStatus.CLOSE,
    )
    jaw_phase = get_mock_put(
        mock_id_controller.apple2().jaw_phase().jaw_phase.user_setpoint
    )

    poly = poly1d(
        DEFAULT_JAW_PHASE_POLY_PARAMS
    )  # default setting for i10 jaw phase to angle
    for cnt, data in enumerate(run_engine_documents["event"]):
        temp_angle = angles[cnt]
        assert data["data"]["mock_id_controller-linear_arbitrary_angle"] == temp_angle
        alpha_real = (
            temp_angle
            if temp_angle > mock_id_controller.angle_threshold_deg
            else temp_angle + 180.0
        )  # convert angle to jawphase.
        assert jaw_phase.call_args_list[cnt] == mock.call(
            str(poly(alpha_real)), wait=True
        )


def test_i10_energy_motor_lookup_idu_convert_csv_to_lookup_success(
    mock_i10_gap_energy_motor_lookup_idu: ConfigServerEnergyMotorLookup,
    mock_i10_phase_energy_motor_lookup_idu: ConfigServerEnergyMotorLookup,
) -> None:
    assert_expected_lut_file_equals_config_server_energy_motor_update_lookup_table(
        EXPECTED_ID_ENERGY_2_GAP_CALIBRATIONS_IDU_JSON,
        mock_i10_gap_energy_motor_lookup_idu,
    )
    assert_expected_lut_file_equals_config_server_energy_motor_update_lookup_table(
        EXPECTED_ID_ENERGY_2_PHASE_CALIBRATIONS_IDU_JSON,
        mock_i10_phase_energy_motor_lookup_idu,
    )


def test_i10_energy_motor_lookup_idd_convert_csv_to_lookup_success(
    mock_i10_gap_energy_motor_lookup_idd: ConfigServerEnergyMotorLookup,
    mock_i10_phase_energy_motor_lookup_idd: ConfigServerEnergyMotorLookup,
) -> None:
    assert_expected_lut_file_equals_config_server_energy_motor_update_lookup_table(
        EXPECTED_ID_ENERGY_2_GAP_CALIBRATIONS_IDD_JSON,
        mock_i10_gap_energy_motor_lookup_idd,
    )
    assert_expected_lut_file_equals_config_server_energy_motor_update_lookup_table(
        EXPECTED_ID_ENERGY_2_PHASE_CALIBRATIONS_IDD_JSON,
        mock_i10_phase_energy_motor_lookup_idd,
    )


@pytest.mark.parametrize("energy", [(100), (5500), (-299)])
async def test_fail_i10_energy_motor_lookup_outside_energy_limits(
    mock_id_controller: I10Apple2Controller,
    energy: float,
):
    with pytest.raises(ValueError) as e:
        await mock_id_controller.energy.set(energy)
    assert str(e.value) == "Demanding energy must lie between {} and {}!".format(
        mock_id_controller.gap_energy_motor_lut.lut.root[
            await mock_id_controller.polarisation_setpoint.get_value()
        ].min_energy,
        mock_id_controller.gap_energy_motor_lut.lut.root[
            await mock_id_controller.polarisation_setpoint.get_value()
        ].max_energy,
    )


async def test_fail_i10_energy_motor_lookup_with_lookup_gap(
    mock_id_controller: I10Apple2Controller,
):
    mock_id_controller.gap_energy_motor_lut.update_lookup_table()
    # make gap in energy
    mock_id_controller.gap_energy_motor_lut.lut.root[Pol.LH] = EnergyCoverage(
        energy_entries=[
            EnergyCoverageEntry(
                min_energy=255.3,
                max_energy=500,
                poly=poly1d([4.33435e-08, -7.52562e-05, 6.41791e-02, 3.88755e00]),
            ),
            EnergyCoverageEntry(
                min_energy=600,
                max_energy=1000,
                poly=poly1d([4.33435e-08, -7.52562e-05, 6.41791e-02, 3.88755e00]),
            ),
        ]
    )
    with pytest.raises(ValueError) as e:
        await mock_id_controller.energy.set(555)
    assert (
        str(e.value)
        == "Cannot find polynomial coefficients for your requested energy."
        + " There might be gap in the calibration lookup table."
    )
