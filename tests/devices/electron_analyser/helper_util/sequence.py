from collections.abc import Sequence

import pytest

from dodal.common.data_util import LoadModelFromJsonFile, ModelLoader, ModelLoaderConfig
from dodal.devices.beamlines import b07, b07_shared, i05, i09
from dodal.devices.electron_analyser.base import BaseRegion
from dodal.devices.electron_analyser.mbs import MbsSequence
from dodal.devices.electron_analyser.specs import SpecsSequence
from dodal.devices.electron_analyser.vgscienta import VGScientaSequence
from tests.devices.electron_analyser.test_data import (
    TEST_MBS_XML_SEQUENCE,
    TEST_SPECS_SEQUENCE,
    TEST_VGSCIENTA_SEQUENCE,
)

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
load_i05_mbs_test_xml_seq = ModelLoader[I05MbsSequence](
    lambda file: I05MbsSequence.from_xml(file),
    ModelLoaderConfig.from_default_file(TEST_MBS_XML_SEQUENCE),
)


def generate_fixture_regions_pair(
    fixture_name: str, regions: Sequence[BaseRegion]
) -> list:
    """Generate a parameterised pytest with a fixture name with the assoicated regions.
    Useful for tests where you need to test each driver or detector with the paried
    sequence file.
    """
    test_cases = []
    for region in regions:
        test_cases.append(
            pytest.param(
                fixture_name,
                region,
                id=f"{fixture_name}-{type(region).__name__}-{region.name}",
            )
        )
    return test_cases
