import os
from typing import Any

from dodal.devices.electron_analyser.abstract import (
    AbstractBaseRegion,
)
from dodal.devices.electron_analyser.specs import (
    SpecsAnalyserDriverIO,
    SpecsDetector,
    SpecsSequence,
)
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaAnalyserDriverIO,
    VGScientaDetector,
    VGScientaSequence,
)

TEST_DATA_PATH = "tests/test_data/electron_analyser/"

TEST_VGSCIENTA_SEQUENCE = os.path.join(TEST_DATA_PATH, "vgscienta_sequence.seq")
TEST_SPECS_SEQUENCE = os.path.join(TEST_DATA_PATH, "specs_sequence.seq")

TEST_SEQUENCES = {
    VGScientaSequence: TEST_VGSCIENTA_SEQUENCE,
    VGScientaDetector: TEST_VGSCIENTA_SEQUENCE,
    VGScientaAnalyserDriverIO: TEST_VGSCIENTA_SEQUENCE,
    SpecsSequence: TEST_SPECS_SEQUENCE,
    SpecsDetector: TEST_SPECS_SEQUENCE,
    SpecsAnalyserDriverIO: TEST_SPECS_SEQUENCE,
}


def get_test_sequence(key: type) -> str:
    for cls in key.__mro__:
        # Check for unscripted class only
        if cls in TEST_SEQUENCES:
            return TEST_SEQUENCES[cls]
    raise KeyError(f"Found no match with type {key}")


TEST_SEQUENCE_REGION_NAMES = ["New_Region", "New_Region1"]


def assert_region_has_expected_values(
    r: AbstractBaseRegion, expected_region_values: dict[str, Any]
) -> None:
    for key in r.__dict__:
        if key in expected_region_values:
            actual = r.__dict__[key]
            expected = expected_region_values[key]
            try:
                assert actual == expected
            except AssertionError as e:
                raise AssertionError(
                    f"Mismatch on key '{key}': actual={actual}, expected={expected}"
                ) from e
        else:
            raise KeyError('key "' + key + '" is not in the expected values.')

    for key in expected_region_values.keys():
        assert r.__dict__.get(key) is not None
