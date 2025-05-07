import pytest
from bluesky import RunEngine
from ophyd_async.testing import set_mock_value

from dodal.devices.electron_analyser.specs import SpecsAnalyserDriverIO, SpecsDetector


@pytest.fixture
def analyser_driver_class() -> type[SpecsAnalyserDriverIO]:
    return SpecsAnalyserDriverIO


async def test_analyser_specs_detector_image_shape(
    sim_analyser: SpecsDetector,
    sequence_file_path: str,
    RE: RunEngine,
) -> None:
    driver = sim_analyser.driver_ref()

    low_energy = 1
    high_energy = 10
    slices = 4
    set_mock_value(driver.low_energy, low_energy)
    set_mock_value(driver.high_energy, high_energy)
    set_mock_value(driver.slices, slices)

    min_angle = 1
    max_angle = 10
    set_mock_value(driver.min_angle_axis, min_angle)
    set_mock_value(driver.max_angle_axis, max_angle)

    angle_axis = await driver.angle_axis.get_value()
    energy_axis = await driver.energy_axis.get_value()

    describe = await sim_analyser.describe()
    assert describe[driver.name + "-image"]["shape"] == [
        len(angle_axis),
        len(energy_axis),
    ]


# ToDo - Check detector configures region correctly when implemented.
