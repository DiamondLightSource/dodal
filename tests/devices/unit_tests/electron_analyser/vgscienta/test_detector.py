import numpy as np
import pytest
from bluesky import RunEngine
from ophyd_async.core import SignalR
from ophyd_async.testing import set_mock_value

from dodal.devices.electron_analyser.vgscienta import (
    VGScientaDetector,
)
from dodal.devices.i09 import LensMode, PassEnergy, PsuMode
from tests.devices.unit_tests.electron_analyser.util import create_analyser_device


@pytest.fixture
def detector_class() -> type[VGScientaDetector[LensMode, PsuMode, PassEnergy]]:
    return VGScientaDetector[LensMode, PsuMode, PassEnergy]


@pytest.fixture
async def sim_detector(
    energy_sources: dict[str, SignalR[float]],
) -> VGScientaDetector[LensMode, PsuMode, PassEnergy]:
    return await create_analyser_device(
        VGScientaDetector[LensMode, PsuMode, PassEnergy],
        energy_sources,
    )


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
