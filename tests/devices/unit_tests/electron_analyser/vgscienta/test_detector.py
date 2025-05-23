import numpy as np
import pytest
from bluesky import RunEngine
from ophyd_async.testing import set_mock_value

from dodal.devices.electron_analyser.vgscienta import (
    VGScientaDetector,
)


@pytest.fixture
def detector_class() -> type[VGScientaDetector]:
    return VGScientaDetector


async def test_analyser_vgscienta_detector_image_shape(
    sim_detector: VGScientaDetector,
    RE: RunEngine,
) -> None:
    driver = sim_detector.driver

    energy_axis = np.array([1, 2, 3, 4, 5])
    angle_axis = np.array([1, 2])
    set_mock_value(driver.energy_axis, energy_axis)
    set_mock_value(driver.angle_axis, angle_axis)

    describe = await sim_detector.describe()
    assert describe[driver.name + "-image"]["shape"] == [
        len(angle_axis),
        len(energy_axis),
    ]


# ToDo - Check detector configures region correctly when implemented.
