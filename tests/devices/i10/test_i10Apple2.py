import pickle
from pathlib import Path

import pytest
from ophyd_async.core import (
    DeviceCollector,
    set_mock_value,
)

from dodal.devices.apple2_undulator import (
    UndlatorPhaseAxes,
    UndulatorGap,
    UndulatorGatestatus,
)
from dodal.devices.i10.i10_pgm import I10Grating
from dodal.devices.i10.id_apple2 import I10Apple2, convert_csv_to_lookup
from dodal.devices.monochromator import PGM


@pytest.fixture
async def mock_id_gap(prefix: str = "BLXX-EA-DET-007:") -> UndulatorGap:
    async with DeviceCollector(mock=True):
        mock_id_gap = UndulatorGap(prefix, "mock_id_gap")
    assert mock_id_gap.name == "mock_id_gap"
    set_mock_value(mock_id_gap.gate, UndulatorGatestatus.close)
    set_mock_value(mock_id_gap.velocity, 1)
    set_mock_value(mock_id_gap.user_readback, 1)
    set_mock_value(mock_id_gap.user_setpoint, "1")
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
    set_mock_value(mock_phaseAxes.top_outer.user_setpoint_readback, 2)
    set_mock_value(mock_phaseAxes.top_inner.user_setpoint_readback, 2)
    set_mock_value(mock_phaseAxes.btm_outer.user_setpoint_readback, 2)
    set_mock_value(mock_phaseAxes.btm_inner.user_setpoint_readback, 2)
    set_mock_value(mock_phaseAxes.top_outer.user_setpoint_demand_readback, 2)
    set_mock_value(mock_phaseAxes.top_inner.user_setpoint_demand_readback, 2)
    set_mock_value(mock_phaseAxes.btm_outer.user_setpoint_demand_readback, 2)
    set_mock_value(mock_phaseAxes.btm_inner.user_setpoint_demand_readback, 2)
    set_mock_value(mock_phaseAxes.fault, 0)
    return mock_phaseAxes


@pytest.fixture
async def mock_pgm(prefix: str = "BLXX-EA-DET-007:") -> PGM:
    async with DeviceCollector(mock=True):
        i10_pgm = PGM(prefix=prefix, grating=I10Grating, gratingPv="NLINES2")
    return i10_pgm


@pytest.fixture
async def mock_id(
    mock_phaseAxes: UndlatorPhaseAxes, mock_id_gap: UndulatorGap, i10_pgm: PGM
) -> I10Apple2:
    async with DeviceCollector(mock=True):
        i10_id = I10Apple2(
            id_gap=mock_id_gap,
            id_phase=mock_phaseAxes,
            energy_gap_table_path=Path(
                "tests/devices/i10/lookupTables/IDEnergy2GapCalibrations.csv"
            ),
            energy_phase_table_path=Path(
                "tests/devices/i10/lookupTables/IDEnergy2PhaseCalibrations.csv"
            ),
            pgm=i10_pgm,
        )
        return i10_id


@pytest.mark.parametrize(
    "fileName, expected_dict, source",
    [
        (
            "tests/devices/i10/lookupTables/IDEnergy2GapCalibrations.csv",
            "tests/devices/i10/lookupTables/expectedIDEnergy2GapCalibrationsIdu.pkl",
            ("Source", "idu"),
        ),
        (
            "tests/devices/i10/lookupTables/IDEnergy2GapCalibrations.csv",
            "tests/devices/i10/lookupTables/expectedIDEnergy2GapCalibrationsIdd.pkl",
            ("Source", "idd"),
        ),
        (
            "tests/devices/i10/lookupTables/IDEnergy2PhaseCalibrations.csv",
            "tests/devices/i10/lookupTables/expectedIDEnergy2PhaseCalibrationsidu.pkl",
            ("Source", "idu"),
        ),
        (
            "tests/devices/i10/lookupTables/IDEnergy2PhaseCalibrations.csv",
            "tests/devices/i10/lookupTables/expectedIDEnergy2PhaseCalibrationsidd.pkl",
            ("Source", "idd"),
        ),
    ],
)
def test_convert_csv_to_lookup(fileName, expected_dict, source):
    data = convert_csv_to_lookup(
        file=fileName,
        source=source,
    )

    with open(expected_dict, "rb") as f:
        loaded_dict = pickle.load(f)
    assert data == loaded_dict
