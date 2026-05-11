from dodal.common.data_util import JsonLoaderConfig, json_model_loader
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


load_b07_specs_test_sequence = json_model_loader(
    SpecsSequence[b07.LensMode, b07_shared.PsuMode],
    JsonLoaderConfig.from_default_file(TEST_SPECS_SEQUENCE),
)
load_i09_vgscienta_test_sequence = json_model_loader(
    VGScientaSequence[i09.LensMode, i09.PsuMode, i09.PassEnergy],
    JsonLoaderConfig.from_default_file(TEST_VGSCIENTA_SEQUENCE),
)


# Map to know what function to load in sequence an analyser driver should use.
TEST_SEQUENCES = {
    SpecsDetector: load_b07_specs_test_sequence,
    SpecsAnalyserDriverIO: load_b07_specs_test_sequence,
    SpecsSequence: load_b07_specs_test_sequence,
    VGScientaDetector: load_i09_vgscienta_test_sequence,
    VGScientaAnalyserDriverIO: load_i09_vgscienta_test_sequence,
    VGScientaSequence: load_i09_vgscienta_test_sequence,
}


def get_test_sequence(key: type):
    for cls in key.__mro__:
        # Check for unscripted class only
        if cls in TEST_SEQUENCES:
            return TEST_SEQUENCES[cls]()
    raise KeyError(f"Found no match with type {key}")
