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
from tests.devices.electron_analyser.test_data import (
    TEST_SPECS_SEQUENCE,
    TEST_VGSCIENTA_SEQUENCE,
)

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


TEST_SEQUENCE_REGION_NAMES = ["New_Region", "New_Region1", "New_Region2"]
