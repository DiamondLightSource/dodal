import numpy as np
from ophyd_async.core import set_mock_value

from dodal.devices.beamlines.i09 import LensMode, PassEnergy, PsuMode
from dodal.devices.electron_analyser.vgscienta import (
    VGScientaDetector,
)


async def test_analyser_vgscienta_detector_image_shape(
    ew4000: VGScientaDetector[LensMode, PsuMode, PassEnergy],
) -> None:
    driver = ew4000.driver
    prefix = driver.name + "-"

    energy_axis = np.array([1, 2, 3, 4, 5])
    angle_axis = np.array([1, 2])
    set_mock_value(driver.energy_axis, energy_axis)
    set_mock_value(driver.angle_axis, angle_axis)

    describe = await ew4000.describe()
    assert describe[f"{prefix}image"]["shape"] == [
        len(angle_axis),
        len(energy_axis),
    ]
