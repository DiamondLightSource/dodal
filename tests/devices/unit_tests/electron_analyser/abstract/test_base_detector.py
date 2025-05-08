import pytest

from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    AbstractBaseRegion,
    AbstractBaseSequence,
    AbstractElectronAnalyserDetector,
)
from dodal.devices.electron_analyser.specs import SpecsDetector
from dodal.devices.electron_analyser.vgscienta import VGScientaDetector
from tests.devices.unit_tests.electron_analyser.test_util import get_test_sequence


@pytest.fixture(params=[SpecsDetector, VGScientaDetector])
def detector_class(
    request: pytest.FixtureRequest,
) -> type[AbstractElectronAnalyserDetector]:
    return request.param


@pytest.fixture
def sequence_file_path(
    sim_detector: AbstractElectronAnalyserDetector[
        AbstractAnalyserDriverIO, AbstractBaseSequence, AbstractBaseRegion
    ],
) -> str:
    return get_test_sequence(type(sim_detector))


def test_analyser_detector_loads_sequence_correctly(
    sim_detector: AbstractElectronAnalyserDetector[
        AbstractAnalyserDriverIO, AbstractBaseSequence, AbstractBaseRegion
    ],
    sequence_file_path: str,
) -> None:
    seq = sim_detector.load_sequence(sequence_file_path)
    assert seq is not None


def test_analyser_detector_creates_region_detectors(
    sim_detector: AbstractElectronAnalyserDetector[
        AbstractAnalyserDriverIO, AbstractBaseSequence, AbstractBaseRegion
    ],
    sequence_file_path: str,
) -> None:
    seq = sim_detector.load_sequence(sequence_file_path)
    region_detectors = sim_detector.create_region_detector_list(sequence_file_path)

    assert len(region_detectors) == len(seq.get_enabled_regions())
    for det in region_detectors:
        assert det.region.enabled is True


# ToDo - Add tests for BaseElectronAnalyserDetector class + controller
# ToDo - Add test that data being read is correct from plan
