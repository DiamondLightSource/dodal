import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.i09_1 import SampleManipulator


@pytest.fixture
def hsmpm() -> SampleManipulator:
    with init_devices(mock=True):
        hsmpm = SampleManipulator("TEST:")
    return hsmpm


@pytest.mark.parametrize(
    "x, y, z, polar, azimuth, tilt",
    [
        (0, 0, 0, 0, 0, 0),
        (1.23, 2.40, 0.0, 0.0, 0.0, 0.0),
        (1.23, 2.40, 3.51, 24.0, 1.0, 2.0),
    ],
)
async def test_hsmpm_positions_and_read(
    hsmpm: SampleManipulator,
    x: float,
    y: float,
    z: float,
    polar: float,
    azimuth: float,
    tilt: float,
) -> None:
    set_mock_value(hsmpm.x.user_readback, x)
    set_mock_value(hsmpm.y.user_readback, y)
    set_mock_value(hsmpm.z.user_readback, z)
    set_mock_value(hsmpm.polar.user_readback, polar)
    set_mock_value(hsmpm.azimuth.user_readback, azimuth)
    set_mock_value(hsmpm.tilt.user_readback, tilt)

    await assert_reading(
        hsmpm,
        {
            "hsmpm-x": partial_reading(x),
            "hsmpm-y": partial_reading(y),
            "hsmpm-z": partial_reading(z),
            "hsmpm-polar": partial_reading(polar),
            "hsmpm-azimuth": partial_reading(azimuth),
            "hsmpm-tilt": partial_reading(tilt),
        },
    )
