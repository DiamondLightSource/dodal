import pytest
from ophyd_async.core import init_devices, set_mock_value
from ophyd_async.testing import assert_reading, partial_reading

from dodal.devices.beamlines.i15_1.gonio_interlock import GonioInterlock


@pytest.fixture
async def interlock() -> GonioInterlock:
    async with init_devices(mock=True):
        interlock = GonioInterlock(bl_prefix="TEST")
    return interlock


async def test_interlock_is_readable(interlock: GonioInterlock):
    await assert_reading(interlock, {f"{interlock.name}-status": partial_reading(0.0)})


# TODO: fix these numbers to be real
@pytest.mark.parametrize(
    "readback, expected_state",
    [
        (65435, True),
        (65440, False),
    ],
)
async def test_interlock_safe_to_operate_logic(
    interlock: GonioInterlock,
    readback: float,
    expected_state: bool,
):
    set_mock_value(interlock.status, readback)
    assert await interlock.shutter_safe_to_operate() is expected_state
