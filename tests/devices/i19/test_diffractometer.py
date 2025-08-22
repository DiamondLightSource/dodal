import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading, set_mock_value

from dodal.devices.i19.diffractometer import DetectorMotion, FourCircleDiffractometer


@pytest.fixture
async def diffractometer() -> FourCircleDiffractometer:
    async with init_devices(mock=True):
        diff = FourCircleDiffractometer("", "test_diffractometer")
    return diff


def test_diffractometer_created_without_errors():
    diff = FourCircleDiffractometer("", "test_diffractometer")
    assert isinstance(diff, FourCircleDiffractometer)
    assert isinstance(diff.det_stage, DetectorMotion)


async def test_positions_can_be_read(diffractometer: FourCircleDiffractometer):
    set_mock_value(diffractometer.det_stage.det_z.user_readback, 250.0)
    set_mock_value(diffractometer.omega.user_readback, -90.0)
    await assert_reading(
        diffractometer,
        {
            "test_diffractometer-x": partial_reading(0.0),
            "test_diffractometer-y": partial_reading(0.0),
            "test_diffractometer-z": partial_reading(0.0),
            "test_diffractometer-phi": partial_reading(0.0),
            "test_diffractometer-kappa": partial_reading(0.0),
            "test_diffractometer-omega": partial_reading(-90.0),
            "test_diffractometer-det_stage-det_z": partial_reading(250.0),
            "test_diffractometer-det_stage-two_theta": partial_reading(0.0),
        },
    )
