import pickle

from dodal.devices.i09_2_shared.i09_apple2 import convert_csv_to_lookup
from tests.devices.i09_2_shared.test_data import (
    TEST_EXPECTED_UNDULATOR_LUT,
    TEST_SOFT_UNDULATOR_LUT,
)


def test_i10_energy_motor_lookup_convert_csv_to_lookup_success():
    data = convert_csv_to_lookup(
        file=TEST_SOFT_UNDULATOR_LUT,
        source=None,
        poly_deg=[
            "9th-order",
            "8th-order",
            "7th-order",
            "6th-order",
            "5th-order",
            "4th-order",
            "3rd-order",
            "2nd-order",
            "1st-order",
            "0th-order",
        ],
    )

    with open(TEST_EXPECTED_UNDULATOR_LUT, "rb") as f:
        loaded_dict = pickle.load(f)
    assert data == loaded_dict
