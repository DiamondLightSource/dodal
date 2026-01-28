import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.i05_1 import XYZPolarAzimuthDefocusStage


@pytest.fixture
def xyzpad_stage() -> XYZPolarAzimuthDefocusStage:
    with init_devices(mock=True):
        xyzpad_stage = XYZPolarAzimuthDefocusStage("TEST:")
    return xyzpad_stage


@pytest.mark.parametrize(
    "x, y, z, polar, azimuth, defocus",
    [
        (0, 0, 0, 0, 0, 0),
        (1.23, 2.40, 0.0, 0.0, 0.0, 0.0),
        (1.23, 2.40, 3.51, 24.0, 1.0, 2.0),
    ],
)
async def test_setting_xyzpad_position_table(
    xyzpad_stage: XYZPolarAzimuthDefocusStage,
    x: float,
    y: float,
    z: float,
    polar: float,
    azimuth: float,
    defocus: float,
) -> None:
    set_mock_value(xyzpad_stage.x.user_readback, x)
    set_mock_value(xyzpad_stage.y.user_readback, y)
    set_mock_value(xyzpad_stage.z.user_readback, z)
    set_mock_value(xyzpad_stage.polar.user_readback, polar)
    set_mock_value(xyzpad_stage.azimuth.user_readback, azimuth)
    set_mock_value(xyzpad_stage.defocus.user_readback, defocus)

    await assert_reading(
        xyzpad_stage,
        {
            "xyzpad_stage-x": partial_reading(x),
            "xyzpad_stage-y": partial_reading(y),
            "xyzpad_stage-z": partial_reading(z),
            "xyzpad_stage-polar": partial_reading(polar),
            "xyzpad_stage-azimuth": partial_reading(azimuth),
            "xyzpad_stage-defoucs": partial_reading(defocus),
        },
    )
