from dodal.common.data_util import load_json_file_to_class
from dodal.devices.beamlines.b07 import (
    B07BSpecs150,
    B07BSpecsAnalyserDriverIO,
    B07BSpecsSequence,
)
from dodal.devices.beamlines.i09 import (
    I09VGScientaAnalyserDriverIO,
    I09VGScientaEW4000,
    I09VGScientaSequence,
)
from tests.devices.electron_analyser.test_data import (
    TEST_SPECS_SEQUENCE,
    TEST_VGSCIENTA_SEQUENCE,
)

TEST_SEQUENCE_REGION_NAMES = ["New_Region", "New_Region1", "New_Region2"]


def b07_specs_test_sequence_loader() -> B07BSpecsSequence:
    return load_json_file_to_class(B07BSpecsSequence, TEST_SPECS_SEQUENCE)


def i09_vgscienta_test_sequence_loader() -> I09VGScientaSequence:
    return load_json_file_to_class(I09VGScientaSequence, TEST_VGSCIENTA_SEQUENCE)


# Map to know what function to load in sequence an analyser driver should use.
TEST_SEQUENCES = {
    B07BSpecs150: b07_specs_test_sequence_loader,
    B07BSpecsAnalyserDriverIO: b07_specs_test_sequence_loader,
    B07BSpecsSequence: b07_specs_test_sequence_loader,
    I09VGScientaEW4000: i09_vgscienta_test_sequence_loader,
    I09VGScientaAnalyserDriverIO: i09_vgscienta_test_sequence_loader,
    I09VGScientaSequence: i09_vgscienta_test_sequence_loader,
}


def get_test_sequence(key: type):
    for cls in key.__mro__:
        # Check for unscripted class only
        if cls in TEST_SEQUENCES:
            return TEST_SEQUENCES[cls]()
    raise KeyError(f"Found no match with type {key}")
