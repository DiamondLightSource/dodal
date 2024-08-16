import pickle

import pytest

from dodal.devices.i10.id_apple2 import convert_csv_to_lookup


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
    print(loaded_dict)
    assert data == loaded_dict
