import numpy as np
import pytest
from bluesky import RunEngine
from ophyd_async.core import init_devices
from ophyd_async.testing import set_mock_value

from dodal.devices.electron_analyser import DualEnergySource
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaDetector,
)
from dodal.devices.i09 import LensMode, PassEnergy, PsuMode
from dodal.testing.electron_analyser import create_detector


@pytest.fixture
async def sim_detector(
    dual_energy_source: DualEnergySource,
    RE: RunEngine,
) -> VGScientaDetector[LensMode, PsuMode, PassEnergy]:
    async with init_devices(mock=True):
        sim_driver = await create_detector(
            VGScientaDetector[LensMode, PsuMode, PassEnergy],
            prefix="TEST:",
            energy_source=dual_energy_source,
        )
    return sim_driver


async def test_analyser_vgscienta_detector_image_shape(
    sim_detector: VGScientaDetector,
) -> None:
    driver = sim_detector.driver
    prefix = driver.name + "-"

    energy_axis = np.array([1, 2, 3, 4, 5])
    angle_axis = np.array([1, 2])
    set_mock_value(driver.energy_axis, energy_axis)
    set_mock_value(driver.angle_axis, angle_axis)

    describe = await sim_detector.describe()
    assert describe[f"{prefix}image"]["shape"] == [
        len(angle_axis),
        len(energy_axis),
    ]
