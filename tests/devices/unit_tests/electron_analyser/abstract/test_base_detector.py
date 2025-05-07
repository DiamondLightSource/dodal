import pytest

from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
    AbstractBaseSequence,
    AbstractElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.specs import SpecsAnalyserDriverIO
from dodal.devices.electron_analyser.vgscienta import VGScientaAnalyserDriverIO
from tests.devices.unit_tests.electron_analyser.test_util import (
    TEST_SPECS_SEQUENCE,
    TEST_VGSCIENTA_SEQUENCE,
)


@pytest.fixture(params=[SpecsAnalyserDriverIO, VGScientaAnalyserDriverIO])
def analyser_driver_class(
    request: pytest.FixtureRequest,
) -> type[AbstractAnalyserDriverIO]:
    return request.param


@pytest.fixture
def sequence_file(analyser_driver_class: type[AbstractAnalyserDriverIO]) -> str:
    if analyser_driver_class == VGScientaAnalyserDriverIO:
        return TEST_VGSCIENTA_SEQUENCE
    elif analyser_driver_class == SpecsAnalyserDriverIO:
        return TEST_SPECS_SEQUENCE
    raise Exception


def test_analyser_detector_loads_sequence_correctly(
    sim_analyser: AbstractElectronAnalyserDetector[
        AbstractAnalyserDriverIO, AbstractBaseSequence, AbstractBaseRegion
    ],
    sequence_file_path: str,
) -> None:
    seq = sim_analyser.load_sequence(sequence_file_path)
    assert seq is not None


def test_analyser_detector_creates_region_detectors(
    sim_analyser: AbstractElectronAnalyserDetector[
        AbstractAnalyserDriverIO, AbstractBaseSequence, AbstractBaseRegion
    ],
    sequence_file_path: str,
) -> None:
    seq = sim_analyser.load_sequence(sequence_file_path)
    region_detectors = sim_analyser.create_region_detector_list(sequence_file_path)

    assert len(region_detectors) == len(seq.get_enabled_regions())
    for det in region_detectors:
        assert det.region.enabled is True
