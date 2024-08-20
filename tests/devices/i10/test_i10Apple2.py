import pickle
from collections import defaultdict
from pathlib import Path
from unittest.mock import Mock

import pytest
from bluesky.plans import scan
from bluesky.run_engine import RunEngine
from numpy import poly1d
from ophyd_async.core import (
    DeviceCollector,
    assert_emitted,
    callback_on_mock_put,
    set_mock_value,
)

from dodal.devices.apple2_undulator import (
    UndlatorPhaseAxes,
    UndulatorGap,
    UndulatorGatestatus,
)
from dodal.devices.i10.i10_pgm import I10Grating
from dodal.devices.i10.id_apple2 import (
    I10Apple2,
    I10Apple2PGM,
    I10Apple2Pol,
    convert_csv_to_lookup,
)
from dodal.devices.monochromator import PGM

IDGAPLOOKUPTABLE = "tests/devices/i10/lookupTables/IDEnergy2GapCalibrations.csv"
IDPHASELOOKUPTABLE = "tests/devices/i10/lookupTables/IDEnergy2PhaseCalibrations.csv"


@pytest.fixture
async def mock_id_gap(prefix: str = "BLXX-EA-DET-007:") -> UndulatorGap:
    async with DeviceCollector(mock=True):
        mock_id_gap = UndulatorGap(prefix, "mock_id_gap")
    assert mock_id_gap.name == "mock_id_gap"
    set_mock_value(mock_id_gap.gate, UndulatorGatestatus.close)
    set_mock_value(mock_id_gap.velocity, 1)
    set_mock_value(mock_id_gap.user_readback, 20)
    set_mock_value(mock_id_gap.user_setpoint, "20")
    set_mock_value(mock_id_gap.fault, 0)
    return mock_id_gap


@pytest.fixture
async def mock_phaseAxes(prefix: str = "BLXX-EA-DET-007:") -> UndlatorPhaseAxes:
    async with DeviceCollector(mock=True):
        mock_phaseAxes = UndlatorPhaseAxes(
            prefix=prefix,
            top_outer="RPQ1",
            top_inner="RPQ2",
            btm_outer="RPQ3",
            btm_inner="RPQ4",
        )
    assert mock_phaseAxes.name == "mock_phaseAxes"
    set_mock_value(mock_phaseAxes.gate, UndulatorGatestatus.close)
    set_mock_value(mock_phaseAxes.top_outer.velocity, 2)
    set_mock_value(mock_phaseAxes.top_inner.velocity, 2)
    set_mock_value(mock_phaseAxes.btm_outer.velocity, 2)
    set_mock_value(mock_phaseAxes.btm_inner.velocity, 2)
    set_mock_value(mock_phaseAxes.top_outer.user_setpoint_readback, 0)
    set_mock_value(mock_phaseAxes.top_inner.user_setpoint_readback, 0)
    set_mock_value(mock_phaseAxes.btm_outer.user_setpoint_readback, 0)
    set_mock_value(mock_phaseAxes.btm_inner.user_setpoint_readback, 0)
    set_mock_value(mock_phaseAxes.top_outer.user_setpoint_demand_readback, 0)
    set_mock_value(mock_phaseAxes.top_inner.user_setpoint_demand_readback, 0)
    set_mock_value(mock_phaseAxes.btm_outer.user_setpoint_demand_readback, 0)
    set_mock_value(mock_phaseAxes.btm_inner.user_setpoint_demand_readback, 0)
    set_mock_value(mock_phaseAxes.fault, 0)
    return mock_phaseAxes


@pytest.fixture
async def mock_pgm(prefix: str = "BLXX-EA-DET-007:") -> PGM:
    async with DeviceCollector(mock=True):
        mock_pgm = PGM(prefix=prefix, grating=I10Grating, gratingPv="NLINES2")
    return mock_pgm


@pytest.fixture
async def mock_id(
    mock_phaseAxes: UndlatorPhaseAxes, mock_id_gap: UndulatorGap
) -> I10Apple2:
    async with DeviceCollector(mock=True):
        mock_id = I10Apple2(
            id_gap=mock_id_gap,
            id_phase=mock_phaseAxes,
            energy_gap_table_path=Path(IDGAPLOOKUPTABLE),
            energy_phase_table_path=Path(IDPHASELOOKUPTABLE),
            source=("Source", "idu"),
        )
        return mock_id


@pytest.fixture
async def mock_id_pgm(mock_id: I10Apple2, mock_pgm: PGM) -> I10Apple2PGM:
    async with DeviceCollector(mock=True):
        mock_id_pgm = I10Apple2PGM(id=mock_id, pgm=mock_pgm)
        set_mock_value(mock_id_pgm.pgm.energy.velocity, 1)
    return mock_id_pgm


@pytest.fixture
async def mock_id_pol(mock_id: I10Apple2, mock_pgm: PGM) -> I10Apple2Pol:
    async with DeviceCollector(mock=True):
        mock_id_pol = I10Apple2Pol(id=mock_id)
    return mock_id_pol


@pytest.mark.parametrize(
    "pol, top_inner_phase,top_outer_phase,btm_inner_phase,btm_outer_phase",
    [
        ("lh", 0, 0, 0, 0),
        ("lv", 24.0, 0, 24.0, 0),
        ("pc", 12, 0, 12, 0),
        ("nc", -12, 0, -12, 0),
        ("la", 12, 0, -12, 0),
        ("la", 0, 12, 0, -12),
        (None, 8, 12, 2, -12),
    ],
)
async def test_I10Apple2_determine_pol(
    mock_id: I10Apple2,
    pol: None | str,
    top_inner_phase: float,
    top_outer_phase: float,
    btm_inner_phase: float,
    btm_outer_phase: float,
):
    set_mock_value(mock_id.phase.top_inner.user_setpoint_readback, top_inner_phase)
    set_mock_value(mock_id.phase.top_outer.user_setpoint_readback, top_outer_phase)
    set_mock_value(mock_id.phase.btm_inner.user_setpoint_readback, btm_inner_phase)
    set_mock_value(mock_id.phase.btm_outer.user_setpoint_readback, btm_outer_phase)

    if pol is None:
        with pytest.raises(ValueError):
            await mock_id.set(800)
    else:
        await mock_id.set(800)

    assert mock_id.pol == pol


async def test_fail_I10Apple2_no_lookup(
    mock_phaseAxes: UndlatorPhaseAxes, mock_id_gap: UndulatorGap
):
    wrong_path = Path("fnslkfndlsnf")
    with pytest.raises(FileNotFoundError) as e:
        I10Apple2(
            id_gap=mock_id_gap,
            id_phase=mock_phaseAxes,
            energy_gap_table_path=wrong_path,
            energy_phase_table_path=Path(IDPHASELOOKUPTABLE),
            source=("Source", "idu"),
        )
    assert str(e.value) == f"Gap look up table is not in path: {wrong_path}"


@pytest.mark.parametrize("energy", [(100), (2500), (-299)])
async def test_fail_I10Apple2_set_outside_energy_limits(
    mock_id: I10Apple2, energy: float
):
    with pytest.raises(ValueError) as e:
        await mock_id.set(energy)
    assert str(e.value) == "Demanding energy must lie between {} and {} eV!".format(
        mock_id.lookup_tables["Gap"][mock_id.pol]["Limit"]["Minimum"],
        mock_id.lookup_tables["Gap"][mock_id.pol]["Limit"]["Maximum"],
    )


async def test_fail_I10Apple2_set_lookup_gap_pol(mock_id: I10Apple2):
    # make gap in energy
    mock_id.lookup_tables["Gap"]["lh"]["Energies"] = {
        "1": {
            "Low": 255.3,
            "High": 500,
            "Poly": poly1d([4.33435e-08, -7.52562e-05, 6.41791e-02, 3.88755e00]),
        }
    }
    mock_id.lookup_tables["Gap"]["lh"]["Energies"] = {
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
        == "Cannot find polynomial coefficients for your requested energy."
        + "There might be gap in the calibration lookup table."
    )


async def test_fail_I10Apple2_set_undefined_pol(mock_id: I10Apple2):
    set_mock_value(mock_id.gap.user_readback, 101)
    with pytest.raises(RuntimeError) as e:
        await mock_id.set(600)
    assert (
        str(e.value)
        == mock_id.name + " is not in use, close gap or set polarisation to use this ID"
    )


async def test_fail_I10Apple2_set_id_not_ready(mock_id: I10Apple2):
    set_mock_value(mock_id.gap.fault, 1)
    with pytest.raises(RuntimeError) as e:
        await mock_id.set(600)
    assert str(e.value) == mock_id.name + " is in fault state"
    set_mock_value(mock_id.gap.fault, 0)
    set_mock_value(mock_id.gap.gate, UndulatorGatestatus.open)
    with pytest.raises(RuntimeError) as e:
        await mock_id.set(600)
    assert str(e.value) == mock_id.name + " is already in motion."


async def test_I10Apple2_RE_scan(mock_id: I10Apple2, RE: RunEngine):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    RE(scan([mock_id], mock_id, 500, 600, num=11), capture_emitted)
    assert_emitted(docs, start=1, descriptor=1, event=11, stop=1)


async def test_I10Apple2_pgm_RE_scan(mock_id_pgm: I10Apple2PGM, RE: RunEngine):
    docs = defaultdict(list)

    def capture_emitted(name, doc):
        docs[name].append(doc)

    mock_id_pgm.id.pol = "lh3"
    RE(scan([mock_id_pgm], mock_id_pgm, 1700, 1800, num=11), capture_emitted)
    assert_emitted(docs, start=1, descriptor=1, event=11, stop=1)
    # with enevery offset
    docs = defaultdict(list)
    await mock_id_pgm.energy_offset.set(20)
    rbv_mocks = Mock()
    rbv_mocks.get.side_effect = range(1700, 1810, 10)
    callback_on_mock_put(
        mock_id_pgm.pgm.energy.user_setpoint,
        lambda *_, **__: set_mock_value(
            mock_id_pgm.pgm.energy.user_readback, rbv_mocks.get()
        ),
    )
    RE(scan([mock_id_pgm], mock_id_pgm, 1700, 1800, num=11), capture_emitted)
    for cnt, data in enumerate(docs["event"]):
        assert data["data"]["mock_id_pgm-id-energy"] == 1700 + cnt * 10 + 20
        assert data["data"]["mock_id_pgm-pgm-energy"] == 1700 + cnt * 10


@pytest.mark.parametrize(
    "pol",
    [("lh"), ("lv"), ("pc"), ("nc"), ("la"), ("dsf")],
)
async def test_I10Apple2_pol_set(mock_id_pol: I10Apple2Pol, pol):
    if pol == "dsf":
        with pytest.raises(ValueError):
            await mock_id_pol.set(pol)
    else:
        await mock_id_pol.set(pol)
        assert mock_id_pol.id.pol == pol


@pytest.mark.parametrize(
    "fileName, expected_dict, source",
    [
        (
            IDGAPLOOKUPTABLE,
            "tests/devices/i10/lookupTables/expectedIDEnergy2GapCalibrationsIdu.pkl",
            ("Source", "idu"),
        ),
        (
            IDGAPLOOKUPTABLE,
            "tests/devices/i10/lookupTables/expectedIDEnergy2GapCalibrationsIdd.pkl",
            ("Source", "idd"),
        ),
        (
            IDPHASELOOKUPTABLE,
            "tests/devices/i10/lookupTables/expectedIDEnergy2PhaseCalibrationsidu.pkl",
            ("Source", "idu"),
        ),
        (
            IDPHASELOOKUPTABLE,
            "tests/devices/i10/lookupTables/expectedIDEnergy2PhaseCalibrationsidd.pkl",
            ("Source", "idd"),
        ),
    ],
)
def test_convert_csv_to_lookup_success(
    fileName: str,
    expected_dict: str,
    source: tuple[str, str],
):
    data = convert_csv_to_lookup(
        file=fileName,
        source=source,
    )

    with open(expected_dict, "rb") as f:
        loaded_dict = pickle.load(f)
    assert data == loaded_dict


def test_convert_csv_to_lookup_failed():
    with pytest.raises(RuntimeError):
        convert_csv_to_lookup(
            file=IDGAPLOOKUPTABLE,
            source=("Source", "idw"),
        )
