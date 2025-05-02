import pytest

from dodal.devices.electron_analyser import (
    ElectronAnalyserDetector,
    SpecsAnalyserDriverIO,
    VGScientaAnalyserDriverIO,
)
from dodal.devices.electron_analyser.abstract_analyser_io import (
    AbstractAnalyserDriverIO,
)
from dodal.devices.electron_analyser.abstract_region import (
    AbstractBaseRegion,
    AbstractBaseSequence,
)
from tests.devices.unit_tests.electron_analyser.test_util import (
    TEST_SPECS_SEQUENCE,
    TEST_VGSCIENTA_SEQUENCE,
)


@pytest.fixture(params=[SpecsAnalyserDriverIO, VGScientaAnalyserDriverIO])
def analyser_class(request: pytest.FixtureRequest) -> type[AbstractAnalyserDriverIO]:
    return request.param


@pytest.fixture
def sequence_file(analyser_class: type[AbstractAnalyserDriverIO]) -> str:
    if analyser_class == VGScientaAnalyserDriverIO:
        return TEST_VGSCIENTA_SEQUENCE
    elif analyser_class == SpecsAnalyserDriverIO:
        return TEST_SPECS_SEQUENCE
    raise Exception


def test_analyser_detector_loads_sequence_correctly(
    sim_analyser: ElectronAnalyserDetector[AbstractBaseSequence, AbstractBaseRegion],
    sequence_file_path: str,
):
    seq = sim_analyser.load_sequence(sequence_file_path)
    assert isinstance(seq, sim_analyser.driver_ref().sequence_type())


def test_analyser_detector_creates_region_detectors(
    sim_analyser: ElectronAnalyserDetector[AbstractBaseSequence, AbstractBaseRegion],
    sequence_file_path: str,
):
    seq = sim_analyser.load_sequence(sequence_file_path)
    region_detectors = sim_analyser.create_region_detectors(sequence_file_path)

    assert len(region_detectors) == len(seq.get_enabled_regions())
    for det in region_detectors:
        assert det.region.enabled is True
