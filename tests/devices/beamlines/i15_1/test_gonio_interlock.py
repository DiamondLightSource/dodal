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
    set_mock_value(interlock.status, 65535)
    await assert_reading(
        interlock,
        {
            f"{interlock.name}-is_safe": partial_reading(True),
            f"{interlock.name}-status": partial_reading(65535),
        },
    )


@pytest.mark.parametrize(
    "readback, expected_state",
    [
        (65535, True),
        (65440, False),
    ],
)
async def test_interlock_safe_to_operate_logic(
    interlock: GonioInterlock,
    readback: float,
    expected_state: bool,
):
    set_mock_value(interlock.status, readback)
    assert await interlock.is_safe.get_value() is expected_state
