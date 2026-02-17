from dodal.common.data_util import load_json_file_to_class
from dodal.devices.beamlines import b07, b07_shared, i09
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

TEST_SEQUENCE_REGION_NAMES = ["New_Region", "New_Region1", "New_Region2"]


def b07_specs_test_sequence_loader() -> SpecsSequence[b07.LensMode, b07_shared.PsuMode]:
    return load_json_file_to_class(
        SpecsSequence[b07.LensMode, b07_shared.PsuMode], TEST_SPECS_SEQUENCE
    )


def i09_vgscienta_test_sequence_loader() -> VGScientaSequence[
    i09.LensMode, i09.PsuMode, i09.PassEnergy
]:
    return load_json_file_to_class(
        VGScientaSequence[i09.LensMode, i09.PsuMode, i09.PassEnergy],
        TEST_VGSCIENTA_SEQUENCE,
    )


# Map to know what function to load in sequence an analyser driver should use.
TEST_SEQUENCES = {
    SpecsDetector: b07_specs_test_sequence_loader,
    SpecsAnalyserDriverIO: b07_specs_test_sequence_loader,
    SpecsSequence: b07_specs_test_sequence_loader,
    VGScientaDetector: i09_vgscienta_test_sequence_loader,
    VGScientaAnalyserDriverIO: i09_vgscienta_test_sequence_loader,
    VGScientaSequence: i09_vgscienta_test_sequence_loader,
}


def get_test_sequence(key: type):
    for cls in key.__mro__:
        # Check for unscripted class only
        if cls in TEST_SEQUENCES:
            return TEST_SEQUENCES[cls]()
    raise KeyError(f"Found no match with type {key}")
