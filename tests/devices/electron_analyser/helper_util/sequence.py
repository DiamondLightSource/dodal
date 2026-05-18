import pytest

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


load_b07_specs_test_sequence = ModelLoader(
    LoadModelFromJsonFile(SpecsSequence[b07.LensMode, b07_shared.PsuMode]),
    ModelLoaderConfig.from_default_file(TEST_SPECS_SEQUENCE),
)
load_i09_vgscienta_test_sequence = ModelLoader(
    LoadModelFromJsonFile(VGScientaSequence[i09.LensMode, i09.PsuMode, i09.PassEnergy]),
    ModelLoaderConfig.from_default_file(TEST_VGSCIENTA_SEQUENCE),
)

load_i05_mbs_test_sequence = ModelLoader(
    LoadModelFromJsonFile(MbsSequence[i05.LensMode, i05.PassEnergy]),
    ModelLoaderConfig.from_default_file(TEST_VGSCIENTA_SEQUENCE),
)

load_i05_mbs_test_xml_sequence = ModelLoader(
    lambda file: MbsSequence[i05.LensMode, i05.PassEnergy].from_xml(file),
    ModelLoaderConfig.from_default_file(
        "tests/devices/electron_analyser/test_data/mbs_region1.arpes"
    ),
)


# Map to know what function to load in sequence an analyser driver should use.
TEST_SEQUENCES = {
    SpecsDetector: load_b07_specs_test_sequence,
    SpecsAnalyserDriverIO: load_b07_specs_test_sequence,
    SpecsSequence: load_b07_specs_test_sequence,
    VGScientaDetector: load_i09_vgscienta_test_sequence,
    VGScientaAnalyserDriverIO: load_i09_vgscienta_test_sequence,
    VGScientaSequence: load_i09_vgscienta_test_sequence,
    MbsSequence: load_i05_mbs_test_xml_sequence,
}


def get_test_sequence(key: type):
    for cls in key.__mro__:
        # Check for unscripted class only
        if cls in TEST_SEQUENCES:
            return TEST_SEQUENCES[cls]()
    raise KeyError(f"Found no match with type {key}")


SEQUENCE_TYPES = [SpecsSequence, VGScientaSequence, MbsSequence]

# # Dynamically build the region test case parameters
# REGION_TEST_CASES = []
# for seq in SEQUENCE_TYPES:
#     sequence = get_test_sequence(seq)
#     for region in sequence.regions:
#         REGION_TEST_CASES.append(
#             pytest.param(
#                 region,
#                 id=f"{type(region).__name__}-{region.name}",
#             )
#         )


def generate_region_test(seq):
    region_test_cases = []
    sequence = get_test_sequence(seq)
    for region in sequence.regions:
        region_test_cases.append(
            pytest.param(
                region,
                id=f"{type(region).__name__}-{region.name}",
            )
        )
    return region_test_cases


REGION_TEST_CASES = [
    generate_region_test(VGScientaSequence),
    generate_region_test(SpecsSequence),
    generate_region_test(MbsSequence),
]


# To Do - Have this work with detector.
# def generate_detector_region_test(detector_name, seq):
#     region_test_cases = []
#     sequence = get_test_sequence(seq)
#     for region in sequence.regions:
#         region_test_cases.append(
#             pytest.param(
#                 detector_name,
#                 region,
#                 id=f"{detector_name}-{type(region).__name__}-{region.name}",
#             )
#         )
#     return region_test_cases


# DETECTOR_WITH_REGION_TEST_CASES = []
