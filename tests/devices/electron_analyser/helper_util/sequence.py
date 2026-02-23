from dodal.common.data_util import JsonModelLoader
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

B07BSpecsSequence = SpecsSequence[b07.LensMode, b07_shared.PsuMode]
I09VGScientaSequence = VGScientaSequence[i09.LensMode, i09.PsuMode, i09.PassEnergy]

TEST_SEQUENCE_REGION_NAMES = ["New_Region", "New_Region1", "New_Region2"]


b07_specs_test_sequence_loader = JsonModelLoader[B07BSpecsSequence](
    B07BSpecsSequence, TEST_SPECS_SEQUENCE
)
i09_vgscienta_test_sequence_loader = JsonModelLoader[I09VGScientaSequence](
    I09VGScientaSequence, TEST_VGSCIENTA_SEQUENCE
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
