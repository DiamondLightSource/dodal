import numpy as np
import pytest
from bluesky import RunEngine
from ophyd_async.testing import set_mock_value

from dodal.devices.electron_analyser.abstract import (
    AbstractAnalyserDriverIO,
    TAbstractElectronAnalyserDetector,
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
    sim_analyser: TAbstractElectronAnalyserDetector,
    sequence_file_path: str,
) -> None:
    seq = sim_analyser.load_sequence(sequence_file_path)
    assert isinstance(seq, sim_analyser.driver_ref().sequence_type())


def test_analyser_detector_creates_region_detectors(
    sim_analyser: TAbstractElectronAnalyserDetector,
    sequence_file_path: str,
) -> None:
    seq = sim_analyser.load_sequence(sequence_file_path)
    region_detectors = sim_analyser.create_region_detector_list(sequence_file_path)

    assert len(region_detectors) == len(seq.get_enabled_regions())
    for det in region_detectors:
        assert det.region.enabled is True


async def test_analyser_vgscienta_detector_image_shape(
    sim_analyser: TAbstractElectronAnalyserDetector,
    sequence_file_path: str,
    RE: RunEngine,
) -> None:
    driver = sim_analyser.driver_ref()

    if driver is not isinstance(driver, VGScientaAnalyserDriverIO):
        pytest.skip("This test only applies to VGScientaAnalyserDriverIO")

    energy_axis = np.array([1, 2, 3, 4, 5])
    angle_axis = np.array([1, 2])
    set_mock_value(driver.energy_axis, energy_axis)
    set_mock_value(driver.angle_axis, angle_axis)

    describe = await sim_analyser.describe()
    assert describe[driver.name + "-image"]["shape"] == [
        len(angle_axis),
        len(energy_axis),
    ]


async def test_analyser_specs_detector_image_shape(
    sim_analyser: TAbstractElectronAnalyserDetector,
    sequence_file_path: str,
    RE: RunEngine,
) -> None:
    driver = sim_analyser.driver_ref()

    if driver is not isinstance(driver, SpecsAnalyserDriverIO):
        pytest.skip("This test only applies to SpecsAnalyserDriverIO")

    low_energy = 1
    high_energy = 10
    slices = 4
    set_mock_value(driver.low_energy, low_energy)
    set_mock_value(driver.high_energy, high_energy)
    set_mock_value(driver.slices, slices)

    # min_angle = 1
    # max_angle = 10
    # set_mock_value(driver.min_angle, min_angle)
    # set_mock_value(driver.high_energy, high_energy)

    # describe = await sim_analyser.describe()
    # assert describe[driver.name + "-image"]["shape"] == [
    #     len(angle_axis),
    #     len(energy_axis),
    # ]
