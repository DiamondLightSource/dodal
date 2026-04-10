import pytest
from ophyd_async.core import init_devices
from ophyd_async.testing import assert_reading, partial_reading

from dodal.common.enums import OpenClosed
from dodal.devices.beamlines.i21 import FastShutterWithLateralMotor


@pytest.fixture
def fs_with_lateral_motor() -> FastShutterWithLateralMotor:
    with init_devices(mock=True):
        fs_with_lateral_motor = FastShutterWithLateralMotor[OpenClosed](
            "TESt", open_state=OpenClosed.OPEN, close_state=OpenClosed.CLOSED
        )
    return fs_with_lateral_motor


async def test_fs_with_lateral_motor_read(
    fs_with_lateral_motor: FastShutterWithLateralMotor,
) -> None:
    await assert_reading(
        fs_with_lateral_motor,
        {
            "fs_with_lateral_motor-shutter_state": partial_reading(OpenClosed.OPEN),
            "fs_with_lateral_motor-x": partial_reading(0),
        },
    )
