from dodal.common.data_util import load_json_file_to_class
from dodal.devices.b07.analyser import (
    B07SpecsAnalyserDriverIO,
    B07SpecsSequence,
)
from dodal.devices.i09.analyser import (
    I09VGScientaAnalyserDriverIO,
    I09VGScientaSequence,
)
from tests.devices.electron_analyser.test_data import (
    TEST_SPECS_SEQUENCE,
    TEST_VGSCIENTA_SEQUENCE,
)

TEST_SEQUENCE_REGION_NAMES = ["New_Region", "New_Region1", "New_Region2"]


def b07_specs_sequence_loader() -> B07SpecsSequence:
    return load_json_file_to_class(B07SpecsSequence, TEST_SPECS_SEQUENCE)


def i09_vgscienta_sequence_loader() -> I09VGScientaSequence:
    return load_json_file_to_class(I09VGScientaSequence, TEST_VGSCIENTA_SEQUENCE)


# Map to know what function to load in sequence an analyser driver should use.
DRIVER_TO_TEST_SEQUENCE = {
    B07SpecsAnalyserDriverIO: b07_specs_sequence_loader(),
    I09VGScientaAnalyserDriverIO: i09_vgscienta_sequence_loader(),
}
