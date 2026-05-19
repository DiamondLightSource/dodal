from dodal.common.data_util import (
    LoadModelFromJsonFile,
    ModelLoader,
    ModelLoaderConfig,
)
from dodal.devices.beamlines import b07, b07_shared, i05, i09
from dodal.devices.electron_analyser.mbs import MbsSequence
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

B07SpecsSequence = SpecsSequence[b07.LensMode, b07_shared.PsuMode]
I09VGScientaSequence = VGScientaSequence[i09.LensMode, i09.PassEnergy]
I05MbsSequence = MbsSequence[i05.LensMode, i05.PassEnergy]


load_b07_specs_test_seq = ModelLoader[B07SpecsSequence](
    LoadModelFromJsonFile(B07SpecsSequence),
    ModelLoaderConfig.from_default_file(TEST_SPECS_SEQUENCE),
)
load_i09_vgscienta_test_seq = ModelLoader[I09VGScientaSequence](
    LoadModelFromJsonFile(I09VGScientaSequence),
    ModelLoaderConfig.from_default_file(TEST_VGSCIENTA_SEQUENCE),
)

load_i05_mbs_test_seq = ModelLoader[I05MbsSequence](
    LoadModelFromJsonFile(I05MbsSequence),
    ModelLoaderConfig.from_default_file(TEST_VGSCIENTA_SEQUENCE),
)

load_i05_mbs_test_xml_seq = ModelLoader[I05MbsSequence](
    lambda file: I05MbsSequence.from_xml(file),
    ModelLoaderConfig.from_default_file(
        "tests/devices/electron_analyser/test_data/mbs_region1.arpes"
    ),
)


# Map to know what function to load in sequence an analyser driver should use.
TEST_SEQUENCES = {
    SpecsDetector: load_b07_specs_test_seq,
    SpecsAnalyserDriverIO: load_b07_specs_test_seq,
    SpecsSequence: load_b07_specs_test_seq,
    VGScientaDetector: load_i09_vgscienta_test_seq,
    VGScientaAnalyserDriverIO: load_i09_vgscienta_test_seq,
    VGScientaSequence: load_i09_vgscienta_test_seq,
    MbsSequence: load_i05_mbs_test_xml_seq,
}


def get_test_sequence(key: type):
    for cls in key.__mro__:
        # Check for unscripted class only
        if cls in TEST_SEQUENCES:
            return TEST_SEQUENCES[cls]()
    raise KeyError(f"Found no match with type {key}")
