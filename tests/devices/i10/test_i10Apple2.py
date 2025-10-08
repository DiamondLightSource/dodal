import os
import pickle
from collections import defaultdict
from unittest import mock
from unittest.mock import MagicMock, Mock

import numpy as np
import pytest
from bluesky.plans import scan
from bluesky.run_engine import RunEngine
from daq_config_server.client import ConfigServer
from numpy import poly1d
from ophyd_async.core import init_devices
from ophyd_async.testing import (
    assert_emitted,
    callback_on_mock_put,
    get_mock_put,
    set_mock_value,
)

from dodal.devices.apple2_undulator import (
    Pol,
    UndulatorGap,
    UndulatorGateStatus,
    UndulatorJawPhase,
    UndulatorPhaseAxes,
)
from dodal.devices.i10.i10_apple2 import (
    DEFAULT_JAW_PHASE_POLY_PARAMS,
    EnergySetter,
    I10Apple2,
    I10Apple2Pol,
    I10EnergyMotorLookup,
    LinearArbitraryAngle,
)
from dodal.devices.i10.i10_setting_data import I10Grating
from dodal.devices.pgm import PGM
from dodal.testing import patch_motor
from tests.devices.i10.test_data import (
    EXPECTED_ID_ENERGY_2_GAP_CALIBRATIONS_IDD_PKL,
    EXPECTED_ID_ENERGY_2_GAP_CALIBRATIONS_IDU_PKL,
    EXPECTED_ID_ENERGY_2_PHASE_CALIBRATIONS_IDD_PKL,
    EXPECTED_ID_ENERGY_2_PHASE_CALIBRATIONS_IDU_PKL,
    ID_ENERGY_2_GAP_CALIBRATIONS_CSV,
    ID_ENERGY_2_PHASE_CALIBRATIONS_CSV,
    LOOKUP_TABLE_PATH,
)

ID_ENERGY_2_GAP_CALIBRATIONS_FILE_CSV = os.path.split(ID_ENERGY_2_GAP_CALIBRATIONS_CSV)[
    1
]


@pytest.fixture
async def mock_id_gap(prefix: str = "BLXX-EA-DET-007:") -> UndulatorGap:
    async with init_devices(mock=True):
        mock_id_gap = UndulatorGap(prefix, "mock_id_gap")
    assert mock_id_gap.name == "mock_id_gap"
    set_mock_value(mock_id_gap.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_id_gap.velocity, 1)
    set_mock_value(mock_id_gap.user_readback, 20)
    set_mock_value(mock_id_gap.user_setpoint, "20")
    set_mock_value(mock_id_gap.fault, 0)
    return mock_id_gap


@pytest.fixture
async def mock_phaseAxes(prefix: str = "BLXX-EA-DET-007:") -> UndulatorPhaseAxes:
    async with init_devices(mock=True):
        mock_phaseAxes = UndulatorPhaseAxes(
            prefix=prefix,
            top_outer="RPQ1",
            top_inner="RPQ2",
            btm_outer="RPQ3",
            btm_inner="RPQ4",
        )
    assert mock_phaseAxes.name == "mock_phaseAxes"
    set_mock_value(mock_phaseAxes.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_phaseAxes.top_outer.velocity, 2)
    set_mock_value(mock_phaseAxes.top_inner.velocity, 2)
    set_mock_value(mock_phaseAxes.btm_outer.velocity, 2)
    set_mock_value(mock_phaseAxes.btm_inner.velocity, 2)
    set_mock_value(mock_phaseAxes.top_outer.user_readback, 0)
    set_mock_value(mock_phaseAxes.top_inner.user_readback, 0)
    set_mock_value(mock_phaseAxes.btm_outer.user_readback, 0)
    set_mock_value(mock_phaseAxes.btm_inner.user_readback, 0)
    set_mock_value(mock_phaseAxes.top_outer.user_setpoint_readback, 0)
    set_mock_value(mock_phaseAxes.top_inner.user_setpoint_readback, 0)
    set_mock_value(mock_phaseAxes.btm_outer.user_setpoint_readback, 0)
    set_mock_value(mock_phaseAxes.btm_inner.user_setpoint_readback, 0)
    set_mock_value(mock_phaseAxes.fault, 0)
    return mock_phaseAxes


@pytest.fixture
async def mock_pgm(prefix: str = "BLXX-EA-DET-007:") -> PGM:
    async with init_devices(mock=True):
        mock_pgm = PGM(prefix=prefix, grating=I10Grating, gratingPv="NLINES2")
    patch_motor(mock_pgm.energy)
    return mock_pgm


@pytest.fixture
async def mock_jaw_phase(prefix: str = "BLXX-EA-DET-007:") -> UndulatorJawPhase:
    async with init_devices(mock=True):
        mock_jaw_phase = UndulatorJawPhase(
            prefix=prefix, move_pv="RPQ1", jaw_phase="JAW"
        )
    set_mock_value(mock_jaw_phase.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_jaw_phase.jaw_phase.velocity, 2)
    set_mock_value(mock_jaw_phase.jaw_phase.user_readback, 0)
    set_mock_value(mock_jaw_phase.fault, 0)
    return mock_jaw_phase


@pytest.fixture
def mock_config_client() -> ConfigServer:
    mock.patch("dodal.devices.i10.i10_apple2.ConfigServer")
    mock_config_client = ConfigServer()
    return mock_config_client


@pytest.fixture
def mock_i10_energy_motor_lookup_idu(
    mock_config_client: ConfigServer,
) -> I10EnergyMotorLookup:
    mock_config_client.get_file_contents = MagicMock(spec=["get_file_contents"])

    def my_side_effect(file_path, reset_cached_result) -> str:
        assert reset_cached_result is True
        with open(file_path) as f:
            return f.read()

    mock_config_client.get_file_contents.side_effect = my_side_effect
    return I10EnergyMotorLookup(
        look_up_table_dir=LOOKUP_TABLE_PATH,
        source=("Source", "idu"),
        config_client=mock_config_client,
    )


@pytest.fixture
async def mock_id(mock_i10_energy_motor_lookup_idu: I10EnergyMotorLookup) -> I10Apple2:
    async with init_devices(mock=True):
        mock_id = I10Apple2(
            prefix="BLWOW-MO-SERVC-01:",
            energy_motor_convertor=mock_i10_energy_motor_lookup_idu.get_motor_from_energy,
        )
    set_mock_value(mock_id.motors.gap.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_id.motors.phase.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_id.id_jaw_phase.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_id.id_jaw_phase.jaw_phase.velocity, 1)
    set_mock_value(mock_id.motors.gap.velocity, 1)
    set_mock_value(mock_id.motors.phase.btm_inner.velocity, 1)
    set_mock_value(mock_id.motors.phase.top_inner.velocity, 1)
    set_mock_value(mock_id.motors.phase.btm_outer.velocity, 1)
    set_mock_value(mock_id.motors.phase.top_outer.velocity, 1)
    return mock_id


@pytest.fixture
async def mock_id_pgm(mock_id: I10Apple2, mock_pgm: PGM) -> EnergySetter:
    async with init_devices(mock=True):
        mock_id_pgm = EnergySetter(id=mock_id, pgm=mock_pgm)
    set_mock_value(mock_id.motors.gap.velocity, 1)
    set_mock_value(mock_id.motors.phase.btm_inner.velocity, 1)
    set_mock_value(mock_id.motors.phase.top_inner.velocity, 1)
    set_mock_value(mock_id.motors.phase.btm_outer.velocity, 1)
    set_mock_value(mock_id.motors.phase.top_outer.velocity, 1)
    set_mock_value(mock_id_pgm.id.id_jaw_phase.jaw_phase.velocity, 1)
    set_mock_value(mock_id_pgm.pgm_ref().energy.velocity, 1)

    set_mock_value(mock_id.motors.gap.gate, UndulatorGateStatus.CLOSE)
    set_mock_value(mock_id_pgm.id.id_jaw_phase.gate, UndulatorGateStatus.CLOSE)

    return mock_id_pgm


@pytest.fixture
async def mock_id_pol(mock_id: I10Apple2) -> I10Apple2Pol:
    async with init_devices(mock=True):
        mock_id_pol = I10Apple2Pol(id=mock_id)

    return mock_id_pol


@pytest.fixture
async def mock_linear_arbitrary_angle(mock_id: I10Apple2) -> LinearArbitraryAngle:
    async with init_devices(mock=True):
        mock_linear_arbitrary_angle = LinearArbitraryAngle(id=mock_id)
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
async def test_i10apple2_determine_pol(
    mock_id: I10Apple2,
    pol: None | str,
    top_inner_phase: float,
    top_outer_phase: float,
    btm_inner_phase: float,
    btm_outer_phase: float,
):
    assert await mock_id.polarisation_setpoint.get_value() == Pol.NONE
    set_mock_value(mock_id.motors.phase.top_inner.user_readback, top_inner_phase)
    set_mock_value(mock_id.motors.phase.top_outer.user_readback, top_outer_phase)
    set_mock_value(mock_id.motors.phase.btm_inner.user_readback, btm_inner_phase)
    set_mock_value(mock_id.motors.phase.btm_outer.user_readback, btm_outer_phase)
    if pol == Pol.NONE:
        with pytest.raises(ValueError):
            await mock_id.set(800)
    else:
        await mock_id.set(800)
        assert await mock_id.polarisation.get_value() == pol


async def test_fail_i10apple2_set_undefined_pol(mock_id: I10Apple2):
    set_mock_value(mock_id.motors.gap.user_readback, 101)
    with pytest.raises(RuntimeError) as e:
        await mock_id.set(600)
    assert (
        str(e.value)
        == mock_id.name + " is not in use, close gap or set polarisation to use this ID"
    )


async def test_fail_i10apple2_set_id_not_ready(mock_id: I10Apple2):
    set_mock_value(mock_id.motors.gap.fault, 1)
    with pytest.raises(RuntimeError) as e:
        await mock_id.set(600)
    assert str(e.value) == mock_id.motors.gap.name + " is in fault state"
    set_mock_value(mock_id.motors.gap.fault, 0)
    set_mock_value(mock_id.motors.gap.gate, UndulatorGateStatus.OPEN)
    with pytest.raises(RuntimeError) as e:
        await mock_id.set(600)
    assert str(e.value) == mock_id.motors.gap.name + " is already in motion."


async def test_i10apple2_RE_scan(mock_id_pgm: EnergySetter, RE: RunEngine):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(scan([], mock_id_pgm.id, 500, 600, num=11), capture_emitted)
    assert_emitted(docs, start=1, descriptor=1, event=11, stop=1)


async def test_energySetter_re_scan(mock_id_pgm: EnergySetter, RE: RunEngine):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    mock_id_pgm.id._set_pol_setpoint(Pol("lh3"))
    RE(scan([], mock_id_pgm, 1700, 1800, num=11), capture_emitted)
    assert_emitted(docs, start=1, descriptor=1, event=11, stop=1)
    # with energy offset
    docs = defaultdict(list)
    await mock_id_pgm.energy_offset.set(20)
    rbv_mocks = Mock()
    rbv_mocks.get.side_effect = range(1700, 1810, 10)
    callback_on_mock_put(
        mock_id_pgm.pgm_ref().energy.user_setpoint,
        lambda *_, **__: set_mock_value(
            mock_id_pgm.pgm_ref().energy.user_readback, rbv_mocks.get()
        ),
    )
    RE(
        scan(
            [],
            mock_id_pgm,
            1700,
            1800,
            num=11,
        ),
        capture_emitted,
    )
    for cnt, data in enumerate(docs["event"]):
        assert data["data"]["mock_id_pgm-id-energy"] == 1700 + cnt * 10 + 20
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
async def test_i10apple2_pol_set(
    mock_id_pol: I10Apple2Pol,
    pol: Pol,
    energy: float,
    expect_top_inner: float,
    expect_top_outer: float,
    expect_btm_inner: float,
    expect_btm_outer: float,
    expect_gap: float,
):
    mock_id_pol.id_ref()._set_energy_rbv(energy)

    if pol == "dsf":
        with pytest.raises(ValueError):
            await mock_id_pol.set(pol)
    else:
        await mock_id_pol.set(pol)

        top_inner = get_mock_put(
            mock_id_pol.id_ref().motors.phase.top_inner.user_setpoint
        )
        top_inner.assert_called_once()
        assert float(top_inner.call_args[0][0]) == pytest.approx(expect_top_inner, 0.01)

        top_outer = get_mock_put(
            mock_id_pol.id_ref().motors.phase.top_outer.user_setpoint
        )
        top_outer.assert_called_once()
        assert float(top_outer.call_args[0][0]) == pytest.approx(expect_top_outer, 0.01)

        btm_inner = get_mock_put(
            mock_id_pol.id_ref().motors.phase.btm_inner.user_setpoint
        )
        btm_inner.assert_called_once()
        assert float(btm_inner.call_args[0][0]) == pytest.approx(expect_btm_inner, 0.01)

        btm_outer = get_mock_put(
            mock_id_pol.id_ref().motors.phase.btm_outer.user_setpoint
        )
        btm_outer.assert_called_once()
        assert float(btm_outer.call_args[0][0]) == pytest.approx(expect_btm_outer, 0.01)

        gap = get_mock_put(mock_id_pol.id_ref().motors.gap.user_setpoint)
        gap.assert_called_once()
        assert float(gap.call_args[0][0]) == pytest.approx(expect_gap, 0.05)


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
async def test_i10apple2_pol_read_check_pol_from_hardware(
    mock_id_pol: I10Apple2Pol,
    pol: str,
    energy: float,
    top_inner: float,
    top_outer: float,
    btm_inner: float,
    btm_outer: float,
):
    mock_id_pol.id_ref()._set_energy_rbv(energy)

    set_mock_value(mock_id_pol.id_ref().motors.phase.top_inner.user_readback, top_inner)
    set_mock_value(mock_id_pol.id_ref().motors.phase.top_outer.user_readback, top_outer)
    set_mock_value(mock_id_pol.id_ref().motors.phase.btm_inner.user_readback, btm_inner)
    set_mock_value(mock_id_pol.id_ref().motors.phase.btm_outer.user_readback, btm_outer)

    assert (await mock_id_pol.read())["mock_id-polarisation"]["value"] == pol


@pytest.mark.parametrize(
    "pol,energy, top_outer, top_inner, btm_inner,btm_outer",
    [
        ("lh3", 500, 0.0, 0.0, 0.0, 0.0),
    ],
)
async def test_i10apple2_pol_read_leave_lh3_unchanged_when_hardware_match(
    mock_id_pol: I10Apple2Pol,
    pol: str,
    energy: float,
    top_inner: float,
    top_outer: float,
    btm_inner: float,
    btm_outer: float,
):
    mock_id_pol.id_ref()._set_energy_rbv(energy)
    mock_id_pol.id_ref()._set_pol_setpoint(Pol("lh3"))
    set_mock_value(mock_id_pol.id_ref().motors.phase.top_inner.user_readback, top_inner)
    set_mock_value(mock_id_pol.id_ref().motors.phase.top_outer.user_readback, top_outer)
    set_mock_value(mock_id_pol.id_ref().motors.phase.btm_inner.user_readback, btm_inner)
    set_mock_value(mock_id_pol.id_ref().motors.phase.btm_outer.user_readback, btm_outer)
    assert (await mock_id_pol.read())["mock_id-polarisation"]["value"] == pol


async def test_linear_arbitrary_pol_fail(
    mock_linear_arbitrary_angle: LinearArbitraryAngle,
):
    with pytest.raises(RuntimeError) as e:
        await mock_linear_arbitrary_angle.set(20)
    assert str(e.value) == (
        f"Angle control is not available in polarisation"
        f" {await mock_linear_arbitrary_angle.id_ref().polarisation.get_value()} with {mock_linear_arbitrary_angle.id_ref().name}"
    )


@pytest.mark.parametrize(
    "poly",
    [18, -18, 12.01, -12.01],
)
async def test_linear_arbitrary_limit_fail(
    mock_linear_arbitrary_angle: LinearArbitraryAngle, poly: float
):
    set_mock_value(
        mock_linear_arbitrary_angle.id_ref().motors.phase.top_inner.user_readback,
        16.4,
    )
    set_mock_value(
        mock_linear_arbitrary_angle.id_ref().motors.phase.top_outer.user_readback, 0
    )
    set_mock_value(
        mock_linear_arbitrary_angle.id_ref().motors.phase.btm_inner.user_readback, 0
    )
    set_mock_value(
        mock_linear_arbitrary_angle.id_ref().motors.phase.btm_outer.user_readback, -16.4
    )
    mock_linear_arbitrary_angle.jaw_phase_from_angle = poly1d([poly])
    with pytest.raises(RuntimeError) as e:
        await mock_linear_arbitrary_angle.set(20)
    assert (
        str(e.value)
        == f"jaw_phase position for angle (20.0) is outside permitted range"
        f" [-{mock_linear_arbitrary_angle.jaw_phase_limit}, {mock_linear_arbitrary_angle.jaw_phase_limit}]"
    )


@pytest.mark.parametrize(
    "start, stop, num_point",
    [
        (-1, 180, 11),
        (-20, 170, 31),
        (-90, -25, 18),
    ],
)
async def test_linear_arbitrary_RE_scan(
    mock_linear_arbitrary_angle: LinearArbitraryAngle,
    RE: RunEngine,
    start: float,
    stop: float,
    num_point: int,
):
    angles = np.linspace(start, stop, num_point, endpoint=True)
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    set_mock_value(
        mock_linear_arbitrary_angle.id_ref().motors.phase.top_inner.user_readback,
        16.4,
    )
    set_mock_value(
        mock_linear_arbitrary_angle.id_ref().motors.phase.top_outer.user_readback, 0
    )
    set_mock_value(
        mock_linear_arbitrary_angle.id_ref().motors.phase.btm_inner.user_readback, 0
    )
    set_mock_value(
        mock_linear_arbitrary_angle.id_ref().motors.phase.btm_outer.user_readback, -16.4
    )
    RE(
        scan(
            [],
            mock_linear_arbitrary_angle,
            start,
            stop,
            num=num_point,
        ),
        capture_emitted,
    )
    assert_emitted(docs, start=1, descriptor=1, event=num_point, stop=1)
    set_mock_value(
        mock_linear_arbitrary_angle.id_ref().motors.gap.gate, UndulatorGateStatus.CLOSE
    )
    set_mock_value(
        mock_linear_arbitrary_angle.id_ref().motors.phase.gate,
        UndulatorGateStatus.CLOSE,
    )
    jaw_phase = get_mock_put(
        mock_linear_arbitrary_angle.id_ref().id_jaw_phase.jaw_phase.user_setpoint
    )

    poly = poly1d(
        DEFAULT_JAW_PHASE_POLY_PARAMS
    )  # default setting for i10 jaw phase to angle
    for cnt, data in enumerate(docs["event"]):
        temp_angle = angles[cnt]
        assert data["data"]["mock_linear_arbitrary_angle-angle"] == temp_angle
        alpha_real = (
            temp_angle
            if temp_angle > mock_linear_arbitrary_angle.angle_threshold_deg
            else temp_angle + 180.0
        )  # convert angle to jawphase.
        assert jaw_phase.call_args_list[cnt] == mock.call(
            str(poly(alpha_real)), wait=True
        )


@pytest.mark.parametrize(
    "fileName, expected_dict_file_name, source",
    [
        (
            ID_ENERGY_2_GAP_CALIBRATIONS_CSV,
            EXPECTED_ID_ENERGY_2_GAP_CALIBRATIONS_IDU_PKL,
            ("Source", "idu"),
        ),
        (
            ID_ENERGY_2_GAP_CALIBRATIONS_CSV,
            EXPECTED_ID_ENERGY_2_GAP_CALIBRATIONS_IDD_PKL,
            ("Source", "idd"),
        ),
        (
            ID_ENERGY_2_PHASE_CALIBRATIONS_CSV,
            EXPECTED_ID_ENERGY_2_PHASE_CALIBRATIONS_IDU_PKL,
            ("Source", "idu"),
        ),
        (
            ID_ENERGY_2_PHASE_CALIBRATIONS_CSV,
            EXPECTED_ID_ENERGY_2_PHASE_CALIBRATIONS_IDD_PKL,
            ("Source", "idd"),
        ),
    ],
)
def test_i10_energy_motor_lookup_convert_csv_to_lookup_success(
    mock_i10_energy_motor_lookup_idu: I10EnergyMotorLookup,
    fileName: str,
    expected_dict_file_name: str,
    source: tuple[str, str],
):
    data = mock_i10_energy_motor_lookup_idu.convert_csv_to_lookup(
        file=fileName,
        source=source,
    )
    with open(expected_dict_file_name, "rb") as f:
        loaded_dict = pickle.load(f)
    assert data == loaded_dict


def test_i10_energy_motor_lookup_convert_csv_to_lookup_failed(
    mock_i10_energy_motor_lookup_idu: I10EnergyMotorLookup,
):
    with pytest.raises(RuntimeError):
        mock_i10_energy_motor_lookup_idu.convert_csv_to_lookup(
            file=ID_ENERGY_2_GAP_CALIBRATIONS_CSV,
            source=("Source", "idw"),
        )


async def test_fail_i10_energy_motor_lookup_no_lookup(
    mock_i10_energy_motor_lookup_idu: I10EnergyMotorLookup,
):
    wrong_path = "fnslkfndlsnf"
    with pytest.raises(FileNotFoundError) as e:
        mock_i10_energy_motor_lookup_idu.convert_csv_to_lookup(
            file=wrong_path,
            source=("Source", "idd"),
        )
    assert str(e.value) == f"[Errno 2] No such file or directory: '{wrong_path}'"


@pytest.mark.parametrize("energy", [(100), (5500), (-299)])
async def test_fail_i10_energy_motor_lookup_outside_energy_limits(
    mock_id: I10Apple2,
    energy: float,
    mock_i10_energy_motor_lookup_idu: I10EnergyMotorLookup,
):
    with pytest.raises(ValueError) as e:
        await mock_id.set(energy)
    assert str(e.value) == "Demanding energy must lie between {} and {} eV!".format(
        mock_i10_energy_motor_lookup_idu.lookup_tables["Gap"][
            await mock_id.polarisation_setpoint.get_value()
        ]["Limit"]["Minimum"],
        mock_i10_energy_motor_lookup_idu.lookup_tables["Gap"][
            await mock_id.polarisation_setpoint.get_value()
        ]["Limit"]["Maximum"],
    )


async def test_fail_i10_energy_motor_lookup_with_lookup_gap(
    mock_id: I10Apple2,
    mock_i10_energy_motor_lookup_idu: I10EnergyMotorLookup,
):
    mock_i10_energy_motor_lookup_idu.update_lookuptable()
    # make gap in energy
    mock_i10_energy_motor_lookup_idu.lookup_tables["Gap"]["lh"]["Energies"] = {
        "1": {
            "Low": 255.3,
            "High": 500,
            "Poly": poly1d([4.33435e-08, -7.52562e-05, 6.41791e-02, 3.88755e00]),
        }
    }
    mock_i10_energy_motor_lookup_idu.lookup_tables["Gap"]["lh"]["Energies"] = {
        "2": {
            "Low": 600,
            "High": 1000,
            "Poly": poly1d([4.33435e-08, -7.52562e-05, 6.41791e-02, 3.88755e00]),
        }
    }
    with pytest.raises(ValueError) as e:
        await mock_id.set(555)
    assert (
        str(e.value)
        == """Cannot find polynomial coefficients for your requested energy.
        There might be gap in the calibration lookup table."""
    )
